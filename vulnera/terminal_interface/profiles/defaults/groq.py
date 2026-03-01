"""
This is an Open Vulnera profile. It configures Open Vulnera to run `Llama 3.1 70B` using Groq.

Make sure to set GROQ_API_KEY environment variable to your API key.
"""

from vulnera import vulnera

vulnera.llm.model = "groq/llama-3.1-70b-versatile"

vulnera.computer.import_computer_api = True

vulnera.llm.supports_functions = False
vulnera.llm.supports_vision = False
vulnera.llm.context_window = 110000
vulnera.llm.max_tokens = 4096
