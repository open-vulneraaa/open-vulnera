"""
This is an Open Vulnera profile to use Cerebras. 

Please set the CEREBRAS_API_KEY environment variable.

See https://inference-docs.cerebras.ai/introduction for more information.
"""

from vulnera import vulnera
import os

# LLM settings
vulnera.llm.api_base = "https://api.cerebras.ai/v1"
vulnera.llm.model = "openai/llama3.1-70b"  # or "openai/Llama-3.1-8B"
vulnera.llm.api_key = os.environ.get("CEREBRAS_API_KEY")
vulnera.llm.supports_functions = False
vulnera.llm.supports_vision = False
vulnera.llm.max_tokens = 4096
vulnera.llm.context_window = 8192


# Computer settings
vulnera.computer.import_computer_api = False

# Misc settings
vulnera.offline = False
vulnera.auto_run = False

# Custom Instructions
vulnera.custom_instructions = f"""

    """
