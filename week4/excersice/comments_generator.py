from models import models, clients
from styles import CSS
import os
import io
import sys
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr
import subprocess
from IPython.display import Markdown, display
from consts import python_hard

system_prompt = f"""
You are a helpful assistant that can improve the code of the user.
The user will provide you with a python code and you will need to add docstring / comments 
and improve the code to help the user understand the code.
Respond only with python code. Do not provide any explanation other than docstring / comments.
"""

def user_prompt_for(python):
    return f"""
Add docstring / comments to the python code to help the user understand the code.
Do not change the code logic, only add comments.
```python
{python}
```
"""

def messages_for(python):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_for(python)}
    ]

def write_output(code):
    with open(f"main.py", "w") as f:
        f.write(code)

def port(model, python):
    client = clients[model]
    reasoning_effort = "high" if 'gpt' in model else None
    response = client.chat.completions.create(model=model, messages=messages_for(python), reasoning_effort=reasoning_effort)
    reply = response.choices[0].message.content
    reply = reply.replace('```python','').replace('```','')
    write_output(reply)
    return reply
    
def run_python(code):
    globals_dict = {"__builtins__": __builtins__}

    buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buffer

    try:
        exec(code, globals_dict)
        output = buffer.getvalue()
    except Exception as e:
        output = f"Error: {e}"
    finally:
        sys.stdout = old_stdout

    return output

with gr.Blocks(css=CSS, theme=gr.themes.Monochrome(), title=f"Add comments to code") as ui:
    with gr.Row(equal_height=True):
        with gr.Column(scale=6):
            original_python = gr.Code(
                label="Python (original)",
                value=python_hard,
                language="python",
                lines=26
            )
        with gr.Column(scale=6):
            commented_python = gr.Code(
                label=f"Python (Commneted)",
                value="",
                language="python",
                lines=26
            )

    with gr.Row(equal_height=True):
        with gr.Column(scale=6):
            python_out = gr.TextArea(label="Python result", lines=8, elem_classes=["py-out"])

    with gr.Row(elem_classes=["controls"]):
        add_comments = gr.Button(f"Comment Code", elem_classes=["convert-btn"])
        python_run = gr.Button("Run Python", elem_classes=["run-btn", "py"])
        model = gr.Dropdown(models, value=models[0], show_label=False)

    add_comments.click(fn=port, inputs=[model, original_python], outputs=[commented_python])
    python_run.click(fn=run_python, inputs=[original_python], outputs=[python_out])

ui.launch(inbrowser=True)
