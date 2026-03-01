"""
This is the template Open Vulnera profile.

A starting point for creating a new profile.

Learn about all the available settings - https://github.com/open-vulnera/open-vulnera/tree/master/docs/settings/all-settings

"""

# Import the vulnera
from vulnera import vulnera

# You can import other libraries too
from datetime import date

# You can set variables
today = date.today()

# LLM Settings
vulnera.llm.model = "groq/llama-3.1-70b-versatile"
vulnera.llm.context_window = 110000
vulnera.llm.max_tokens = 4096
vulnera.llm.api_base = "https://api.example.com"
vulnera.llm.api_key = "your_api_key_here"
vulnera.llm.supports_functions = False
vulnera.llm.supports_vision = False


# Vulnera Settings
vulnera.offline = False
vulnera.loop = True
vulnera.auto_run = False

# Toggle OS Mode - https://github.com/open-vulnera/open-vulnera/tree/master/docs/guides/os-mode
vulnera.os = False

# Import Computer API - https://github.com/open-vulnera/open-vulnera/tree/master/docs/code-execution/computer-api
vulnera.computer.import.computer_api = True


# Set Custom Instructions to improve your Vulnera's performance at a given task
vulnera.custom_instructions = f"""
    Today's date is {today}.
    """
