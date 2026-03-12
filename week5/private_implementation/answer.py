from openai import OpenAI
from dotenv import load_dotenv
from chromadb import PersistentClient
from litellm import completion
import litellm
from pydantic import BaseModel, Field
from pathlib import Path
from tenacity import retry, wait_exponential


load_dotenv(override=True)

MODEL = "openai/gpt-4.1-nano"
# MODEL = "groq/openai/gpt-oss-120b"
DB_NAME = str(Path(__file__).parent.parent / "preprocessed_db")
KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "knowledge-base"
SUMMARIES_PATH = Path(__file__).parent.parent / "summaries"

collection_name = "docs"
embedding_model = "text-embedding-3-large"
wait = wait_exponential(multiplier=1, min=10, max=240)

openai = OpenAI()

chroma = PersistentClient(path=DB_NAME)
collection = chroma.get_or_create_collection(collection_name)

RETRIEVAL_K = 20
FINAL_K = 10
QUERIES_K = 3

SUMMARY_K = 5
TOP_SOURCES = 2
CHUNKS_PER_SOURCE = 15

SYSTEM_PROMPT = """
You are a knowledgeable, friendly assistant representing the company Insurellm.
You are chatting with a user about Insurellm.
Your answer will be evaluated for accuracy, relevance and completeness, so make sure it only answers the question and fully answers it.
If you don't know the answer, say so.
For context, here are specific extracts from the Knowledge Base that might be directly relevant to the user's question:
{context}

With this context, please answer the user's question. Be accurate, relevant and complete.
"""


class Result(BaseModel):
    page_content: str
    metadata: dict


class RankOrder(BaseModel):
    order: list[int] = Field(
        description="The order of relevance of chunks, from most relevant to least relevant, by chunk id number"
    )


@retry(wait=wait)
def rerank(question, chunks):
    system_prompt = """
You are a document re-ranker.
You are provided with a question and a list of relevant chunks of text from a query of a knowledge base.
The chunks are provided in the order they were retrieved; this should be approximately ordered by relevance, but you may be able to improve on that.
You must rank order the provided chunks by relevance to the question, with the most relevant chunk first.
Reply only with the list of ranked chunk ids, nothing else. Include all the chunk ids you are provided with, reranked.
"""
    user_prompt = f"The user has asked the following question:\n\n{question}\n\nOrder all the chunks of text by relevance to the question, from most relevant to least relevant. Include all the chunk ids you are provided with, reranked.\n\n"
    user_prompt += "Here are the chunks:\n\n"
    for index, chunk in enumerate(chunks):
        user_prompt += f"# CHUNK ID: {index + 1}:\n\n{chunk.page_content}\n\n"
    user_prompt += "Reply only with the list of ranked chunk ids, nothing else."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    response = completion(model=MODEL, messages=messages, response_format=RankOrder)
    reply = response.choices[0].message.content
    order = RankOrder.model_validate_json(reply).order
    return [chunks[i - 1] for i in order]


def make_rag_messages(question, history, chunks):
    context = "\n\n".join(
        f"Extract from {chunk.metadata['source']}:\n{chunk.page_content}" for chunk in chunks
    )
    system_prompt = SYSTEM_PROMPT.format(context=context)
    return (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": question}]
    )


@retry(wait=wait)
def rewrite_query(question, history=[], rewritten_questions=[]):
    """Rewrite the user's question into a short, specific query that is most likely to surface relevant passages from the books Knowledge Base."""
    previous = "\n".join(f"- {q}" for q in rewritten_questions) if rewritten_questions else "(none)"
    message = f"""
You are in a conversation with a user, answering questions about the company Insurellm.
You are about to look up information in a Knowledge Base to answer the user's question.

Conversation history:
{history}

User's current question:
{question}

Previously generated search queries (do NOT repeat these exactly):
{previous}

Respond only with a short, refined question that you will use to search the Knowledge Base.
It should be a VERY short specific question most likely to surface content. Focus on the question details.
IMPORTANT: Respond ONLY with the precise knowledgebase query, nothing else.
"""
    response = completion(model=MODEL, messages=[{"role": "system", "content": message}])
    return response.choices[0].message.content


def merge_chunks(chunks):
    merged = []
    for chunk_list in chunks:
        for chunk in chunk_list:
            if chunk not in merged:
                merged.append(chunk) 
    return merged



def fetch_context_unranked(question):
    query = openai.embeddings.create(model=embedding_model, input=[question]).data[0].embedding
    results = collection.query(query_embeddings=[query], n_results=RETRIEVAL_K)
    chunks = []
    for result in zip(results["documents"][0], results["metadatas"][0]):
        chunks.append(Result(page_content=result[0], metadata=result[1]))
    return chunks


def fetch_context(original_question, history=[]):
    different_questions = [original_question]
    different_chunks = [fetch_context_unranked(original_question)]
    for i in range(QUERIES_K):
        tempruary_question = rewrite_query(original_question, history, different_questions)
        different_questions.append(tempruary_question)
        different_chunks.append(fetch_context_unranked(tempruary_question))
    print(different_chunks)
    chunks = merge_chunks(different_chunks)
    print(chunks)
    reranked = rerank(original_question, chunks)
    return reranked[:FINAL_K]

def fetch_context_hierarchical(original_question, history=[]):
    different_questions = [original_question]
    for i in range(QUERIES_K):
        tempruary_question = rewrite_query(original_question, history, different_questions)
        different_questions.append(tempruary_question)
        
    all_summaries = []
    for i in different_questions:
        all_summaries.append(fetch_summaries_unranked(i))
    summaries = merge_chunks(all_summaries)

    top_sources = pick_top_sources_from_summaries(summaries, original_question)

    all_chunks = []
    for q in different_questions:
        all_chunks.append(fetch_chunks_for_sources(q, top_sources))
    chunks = merge_chunks(all_chunks)

    reranked = rerank(original_question, chunks)
    return reranked[:FINAL_K]

def fetch_summaries_unranked(question):
    query = openai.embeddings.create(model=embedding_model, input=[question]).data[0].embedding
    results = collection.query(
        query_embeddings=[query],
        n_results=SUMMARY_K,
        where={"level": "summary"},
    )
    summaries = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        summaries.append(Result(page_content=doc, metadata=meta))
    return summaries

def pick_top_sources_from_summaries(summaries, question):
    ranked_summaries = rerank(summaries, question)
    sources = []
    for s in ranked_summaries:
        src = s.metadata.get("source")
        if src and src not in sources:
            sources.append(src)
        if len(sources) >= TOP_SOURCES:
            break
    return sources


def fetch_chunks_for_sources(question, sources):
    query = openai.embeddings.create(model=embedding_model, input=[question]).data[0].embedding
    chunks = []
    for src in sources:
        results = collection.query(
            query_embeddings=[query],
            n_results=CHUNKS_PER_SOURCE,
            where={"level": "chunk", "source": src},
        )
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            chunks.append(Result(page_content=doc, metadata=meta))
    return chunks


@retry(wait=wait)
def answer_question(question: str, history: list[dict] = []) -> tuple[str, list]:
    """
    Answer a question using RAG and return the answer and the retrieved context
    """
    chunks = fetch_context(question)
    messages = make_rag_messages(question, history, chunks)
    response = completion(model=MODEL, messages=messages)
    return response.choices[0].message.content, chunks
