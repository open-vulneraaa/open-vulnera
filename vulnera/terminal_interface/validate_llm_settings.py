"""
I do not like this and I want to get rid of it lol. Like, what is it doing..?
I guess it's setting up the model. So maybe this should be like, vulnera.llm.load() soon!!!!!!!
"""

import os
import subprocess
import time

os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
import litellm
from prompt_toolkit import prompt

from vulnera.terminal_interface.contributing_conversations import (
    contribute_conversation_launch_logic,
)


def validate_llm_settings(vulnera):
    """
    Interactively prompt the user for required LLM settings
    """

    # This runs in a while loop so `continue` lets us start from the top
    # after changing settings (like switching to/from local)
    while True:
        if vulnera.offline:
            # We have already displayed a message.
            # (This strange behavior makes me think validate_llm_settings needs to be rethought / refactored)
            break

        else:
            # Ensure API keys are set as environment variables

            # OpenAI
            if vulnera.llm.model in [
                "gpt-4",
                "gpt-3.5-turbo",
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
            ]:
                if (
                    not os.environ.get("OPENAI_API_KEY")
                    and not vulnera.llm.api_key
                    and not vulnera.llm.api_base
                ):
                    display_welcome_message_once(vulnera)

                    vulnera.display_message(
                        """---
                    > OpenAI API key not found

                    To use `gpt-4o` (recommended) please provide an OpenAI API key.

                    To use another language model, run `vulnera --local` or consult the documentation at [GitHub](https://github.com/open-vulnera/open-vulnera/tree/master/docs/language-models).
                    
                    ---
                    """
                    )

                    response = prompt("OpenAI API key: ", is_password=True)

                    if response == "vulnera --local":
                        print(
                            "\nType `vulnera --local` again to use a local language model.\n"
                        )
                        exit()

                    vulnera.display_message(
                        """

                    **Tip:** To save this key for later, run one of the following and then restart your terminal. 
                    MacOS: `echo 'export OPENAI_API_KEY=your_api_key' >> ~/.zshrc`
                    Linux: `echo 'export OPENAI_API_KEY=your_api_key' >> ~/.bashrc`
                    Windows: `setx OPENAI_API_KEY your_api_key`
                    
                    ---"""
                    )

                    vulnera.llm.api_key = response
                    time.sleep(2)
                    break

            # This is a model we don't have checks for yet.
            break

    # If we're here, we passed all the checks.

    # Auto-run is for fast, light usage -- no messages.
    # If offline, it's usually a bogus model name for LiteLLM since LM Studio doesn't require one.
    # If (len(vulnera.messages) == 1), they probably used the advanced "i .command}" entry, so no message should be displayed.
    if (
        not vulnera.auto_run
        and not vulnera.offline
        and not (len(vulnera.messages) == 1)
    ):
        vulnera.display_message(f"> Model set to `{vulnera.llm.model}`")
    if len(vulnera.messages) == 1:
        # Special message for "i .command}" usage
        # vulnera.display_message(f"\n*{vulnera.llm.model} via Open Vulnera:*")
        pass

    if "ollama" in vulnera.llm.model:
        vulnera.llm.load()
    return


def display_welcome_message_once(vulnera):
    """
    Displays a welcome message only on its first call.

    (Uses an internal attribute `_displayed` to track its state.)
    """
    if not hasattr(display_welcome_message_once, "_displayed"):
        vulnera.display_message(
            """
        ●

        Welcome to **Open Vulnera**.
        """
        )
        time.sleep(1)

        display_welcome_message_once._displayed = True
