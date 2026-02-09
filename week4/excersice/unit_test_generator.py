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
You are a helpful assitant that create unit tests for the user code.
The user will provide you with a python code and you will need to create and add unit tests for the entire code.
Do not change the code logic, Just return the required unit tests the tests the code correctlly.
Respond only with unit tests in python code. Do not provide any explanation and do not retrun the user code.
"""

def user_prompt_for(python):
    return f"""
Add unit tests to the python code to help the user test the code.
Do not change the code logic.
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

with gr.Blocks(css=CSS, theme=gr.themes.Monochrome(), title=f"Create unit tests to code") as ui:
    with gr.Row(equal_height=True):
        with gr.Column(scale=6):
            python = gr.Code(
                label="Python Code",
                value=python_hard,
                language="python",
                lines=26
            )
        with gr.Column(scale=6):
            unit_tests = gr.Code(
                label=f"Unit Tests",
                value="",
                language="python",
                lines=26
            )

    with gr.Row(equal_height=True):
        with gr.Column(scale=6):
            python_out = gr.TextArea(label="Python output", lines=8, elem_classes=["py-out"])
        with gr.Column(scale=6):
            unit_test_out = gr.TextArea(label="Unit tests output", lines=8, elem_classes=["py-out"])

    with gr.Row(elem_classes=["controls"]):
        python_run = gr.Button("Run Python", elem_classes=["run-btn", "py"])
        model = gr.Dropdown(models, value=models[0], show_label=False)
        add_comments = gr.Button(f"Create Unit Tests", elem_classes=["convert-btn"])
        unit_tests_run = gr.Button("Run Tests", elem_classes=["run-btn", "py"])

    add_comments.click(fn=port, inputs=[model, python], outputs=[unit_tests])
    python_run.click(fn=run_python, inputs=[python], outputs=[python_out])
    unit_tests_run.click(fn=run_python, inputs=[unit_tests], outputs=[unit_test_out])

ui.launch(inbrowser=True)
