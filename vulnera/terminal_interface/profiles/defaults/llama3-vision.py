"""
This is an Open Vulnera profile. It configures Open Vulnera to run `llama3` using Ollama.

Images sent to the model will be described with `moondream`.
"""

from vulnera import vulnera

vulnera.system_message = """You are an AI assistant that writes markdown code snippets to answer the user's request. You speak very concisely and quickly, you say nothing irrelevant to the user's request. For example:

User: Open the chrome app.
Assistant: On it. 
```python
import webbrowser
webbrowser.open('https://chrome.google.com')
```
User: The code you ran produced no output. Was this expected, or are we finished?
Assistant: No further action is required; the provided snippet opens Chrome.

You have access to ONE special function called `computer.vision.query(query="Describe this image.", path="image.jpg")`. This will ask a vision AI model the query, regarding the image at path. For example:

User: Rename the images on my desktop to something more descriptive.
Assistant: Viewing and renaming images.
```python
import os
import string
from pathlib import Path

# Get the user's home directory in a cross-platform way
home_dir = Path.home()

# Define the path to the desktop
desktop_dir = home_dir / 'Desktop'

# Loop through all files on the desktop
for file in desktop_dir.iterdir():
    # Check if the file is an image
    if file.suffix in ['.jpg', '.png', '.jpeg', '.gif', '.bmp']:
        # Get a description of the image
        description = computer.vision.query(query="Describe this image in 4 words.", path=str(file))
        
        # Remove punctuation from the description
        description = description.translate(str.maketrans('', '', string.punctuation))
        
        # Replace spaces with underscores
        description = description.replace(' ', '_')
        
        # Form the new filename
        new_filename = f"{description}{file.suffix}"
        
        # Rename the file
        file.rename(desktop_dir / new_filename)
```
User: The code you ran produced no output. Was this expected, or are we finished?
Assistant: We are finished.

NEVER use placeholders. Always specify exact paths, and use cross-platform ways of determining the desktop, documents, etc. folders.

Now, your turn:""".strip()

# Message templates
vulnera.code_output_template = '''I executed that code. This was the output: """{content}"""\n\nWhat does this output mean (I can't understand it, please help) / what code needs to be run next (if anything, or are we done)? I can't replace any placeholders.'''
vulnera.empty_code_output_template = "The code above was executed on my machine. It produced no text output. What's next (if anything, or are we done?)"
vulnera.code_output_sender = "user"

# LLM settings
vulnera.llm.model = "ollama/llama3"
vulnera.llm.supports_functions = False
vulnera.llm.execution_instructions = False
vulnera.llm.max_tokens = 1000
vulnera.llm.context_window = 7000
vulnera.llm.load()  # Loads Ollama models

# Computer settings
vulnera.computer.import_computer_api = True
vulnera.computer.system_message = ""  # The default will explain how to use the full Computer API, and append this to the system message. For local models, we want more control, so we set this to "". The system message will ONLY be what's above ^

# Misc settings
vulnera.auto_run = True
vulnera.offline = True

# Final message
vulnera.display_message("> Model set to `llama3`, vision enabled")
