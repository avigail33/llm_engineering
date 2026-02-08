from models import models, clients

system_prompt = f"""
You are a helpful assistant that can improve the code of the user.
The user will provide you with a code and you will need to add docstring / comments 
and improve the code to help the user understand the code.
"""

def user_prompt_for(python):
    return f"""
Add docstring / comments to the code to help the user understand the code.
```python
{python}
```
"""

def messages_for(python):
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt_for(python)}
    ]
 