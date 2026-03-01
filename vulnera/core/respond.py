import json
import os
import re
import time
import traceback

os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
import litellm

from ..terminal_interface.utils.display_markdown_message import display_markdown_message
from .render_message import render_message


def respond(vulnera):
    """
    Yields chunks.
    Responds until it decides not to run any more code or say anything else.
    """

    last_unsupported_code = ""
    insert_loop_message = False

    while True:
        ## RENDER SYSTEM MESSAGE ##

        system_message = vulnera.system_message

        # Add language-specific system messages
        for language in vulnera.computer.terminal.languages:
            if hasattr(language, "system_message"):
                system_message += "\n\n" + language.system_message

        # Add custom instructions
        if vulnera.custom_instructions:
            system_message += "\n\n" + vulnera.custom_instructions

        # Add computer API system message
        if vulnera.computer.import_computer_api:
            if vulnera.computer.system_message not in system_message:
                system_message = (
                    system_message + "\n\n" + vulnera.computer.system_message
                )

        # Storing the messages so they're accessible in the vulnera's computer
        # no... this is a huge time sink.....
        # if vulnera.sync_computer:
        #     output = vulnera.computer.run(
        #         "python", f"messages={vulnera.messages}"
        #     )

        ## Rendering ↓
        rendered_system_message = render_message(vulnera, system_message)
        ## Rendering ↑

        rendered_system_message = {
            "role": "system",
            "type": "message",
            "content": rendered_system_message,
        }

        # Create the version of messages that we'll send to the LLM
        messages_for_llm = vulnera.messages.copy()
        messages_for_llm = [rendered_system_message] + messages_for_llm

        if insert_loop_message:
            messages_for_llm.append(
                {
                    "role": "user",
                    "type": "message",
                    "content": loop_message,
                }
            )
            # Yield two newlines to separate the LLMs reply from previous messages.
            yield {"role": "assistant", "type": "message", "content": "\n\n"}
            insert_loop_message = False

        ### RUN THE LLM ###

        assert (
            len(vulnera.messages) > 0
        ), "User message was not passed in. You need to pass in at least one message."

        if (
            vulnera.messages[-1]["type"] != "code"
        ):  # If it is, we should run the code (we do below)
            try:
                for chunk in vulnera.llm.run(messages_for_llm):
                    yield {"role": "assistant", **chunk}

            except litellm.exceptions.BudgetExceededError:
                vulnera.display_message(
                    f"""> Max budget exceeded

                    **Session spend:** ${litellm._current_cost}
                    **Max budget:** ${vulnera.max_budget}

                    Press CTRL-C then run `vulnera --max_budget [higher USD amount]` to proceed.
                """
                )
                break

            except Exception as e:
                error_message = str(e).lower()
                if (
                    vulnera.offline == False
                    and ("auth" in error_message or
                         "api key" in error_message)
                ):
                    # Provide extra information on how to change API keys, if
                    # we encounter that error (Many people writing GitHub
                    # issues were struggling with this)
                    output = traceback.format_exc()
                    raise Exception(
                        f"{output}\n\nThere might be an issue with your API key(s).\n\nTo reset your API key (we'll use OPENAI_API_KEY for this example, but you may need to reset your ANTHROPIC_API_KEY, HUGGINGFACE_API_KEY, etc):\n        Mac/Linux: 'export OPENAI_API_KEY=your-key-here'. Update your ~/.zshrc on MacOS or ~/.bashrc on Linux with the new key if it has already been persisted there.,\n        Windows: 'setx OPENAI_API_KEY your-key-here' then restart terminal.\n\n"
                    )
                elif (
                    isinstance(e, litellm.exceptions.RateLimitError)
                    and ("exceeded" in str(e).lower() or
                         "insufficient_quota" in str(e).lower())
                ):
                    display_markdown_message(
                        f""" > You ran out of current quota for OpenAI's API, please check your plan and billing details. You can either wait for the quota to reset or upgrade your plan.

                        To check your current usage and billing details, visit the [OpenAI billing page](https://platform.openai.com/settings/organization/billing/overview).

                        You can also use `vulnera --max_budget [higher USD amount]` to set a budget for your sessions.
                        """
                    )

                elif (
                    vulnera.offline == False and "not have access" in str(e).lower()
                ):
                    # The previous behavior offered a hosted 'i' model provided by
                    # the original Open Interpreter project. That hosted model and
                    # associated flows have been removed during rebranding.
                    # Instead, surface a helpful error asking the user to verify
                    # their model name and API credentials.
                    raise Exception(
                        f"The model '{vulnera.llm.model}' is invalid or you do not have access. Please verify the model name and your API credentials for the provider you are using."
                    )
                elif vulnera.offline and not vulnera.os:
                    raise
                else:
                    raise

        ### RUN CODE (if it's there) ###

        if vulnera.messages[-1]["type"] == "code":
            if vulnera.verbose:
                print("Running code:", vulnera.messages[-1])

            try:
                # What language/code do you want to run?
                language = vulnera.messages[-1]["format"].lower().strip()
                code = vulnera.messages[-1]["content"]

                if code.startswith("`\n"):
                    code = code[2:].strip()
                    if vulnera.verbose:
                        print("Removing `\n")
                    vulnera.messages[-1]["content"] = code  # So the LLM can see it.

                # A common hallucination
                if code.startswith("functions.execute("):
                    edited_code = code.replace("functions.execute(", "").rstrip(")")
                    try:
                        code_dict = json.loads(edited_code)
                        language = code_dict.get("language", language)
                        code = code_dict.get("code", code)
                        vulnera.messages[-1][
                            "content"
                        ] = code  # So the LLM can see it.
                        vulnera.messages[-1][
                            "format"
                        ] = language  # So the LLM can see it.
                    except:
                        pass

                # print(code)
                # print("---")
                # time.sleep(2)

                if code.strip().endswith("executeexecute"):
                    code = code.replace("executeexecute", "")
                    try:
                        vulnera.messages[-1][
                            "content"
                        ] = code  # So the LLM can see it.
                    except:
                        pass

                if code.replace("\n", "").replace(" ", "").startswith('{"language":'):
                    try:
                        code_dict = json.loads(code)
                        if set(code_dict.keys()) == {"language", "code"}:
                            language = code_dict["language"]
                            code = code_dict["code"]
                            vulnera.messages[-1][
                                "content"
                            ] = code  # So the LLM can see it.
                            vulnera.messages[-1][
                                "format"
                            ] = language  # So the LLM can see it.
                    except:
                        pass

                if code.replace("\n", "").replace(" ", "").startswith("{language:"):
                    try:
                        code = code.replace("language: ", '"language": ').replace(
                            "code: ", '"code": '
                        )
                        code_dict = json.loads(code)
                        if set(code_dict.keys()) == {"language", "code"}:
                            language = code_dict["language"]
                            code = code_dict["code"]
                            vulnera.messages[-1][
                                "content"
                            ] = code  # So the LLM can see it.
                            vulnera.messages[-1][
                                "format"
                            ] = language  # So the LLM can see it.
                    except:
                        pass

                if (
                    language == "text"
                    or language == "markdown"
                    or language == "plaintext"
                ):
                    # It does this sometimes just to take notes. Let it, it's useful.
                    # In the future we should probably not detect this behavior as code at all.
                    real_content = vulnera.messages[-1]["content"]
                    vulnera.messages[-1] = {
                        "role": "assistant",
                        "type": "message",
                        "content": f"```\n{real_content}\n```",
                    }
                    continue

                # Is this language enabled/supported?
                if vulnera.computer.terminal.get_language(language) is None:
                    output = f"`{language}` disabled or not supported."

                    yield {
                        "role": "computer",
                        "type": "console",
                        "format": "output",
                        "content": output,
                    }

                    # Let the response continue so it can deal with the unsupported code in another way. Also prevent looping on the same piece of code.
                    if code != last_unsupported_code:
                        last_unsupported_code = code
                        continue
                    else:
                        break

                # Is there any code at all?
                if code.strip() == "":
                    yield {
                        "role": "computer",
                        "type": "console",
                        "format": "output",
                        "content": "Code block was empty. Please try again, be sure to write code before executing.",
                    }
                    continue

                # Yield a message, such that the user can stop code execution if they want to
                try:
                    yield {
                        "role": "computer",
                        "type": "confirmation",
                        "format": "execution",
                        "content": {
                            "type": "code",
                            "format": language,
                            "content": code,
                        },
                    }
                except GeneratorExit:
                    # The user might exit here.
                    # We need to tell python what we (the generator) should do if they exit
                    break

                # They may have edited the code! Grab it again
                code = [m for m in vulnera.messages if m["type"] == "code"][-1][
                    "content"
                ]

                # don't let it import computer — we handle that!
                if vulnera.computer.import_computer_api and language == "python":
                    code = code.replace("import computer\n", "pass\n")
                    code = re.sub(
                        r"import computer\.(\w+) as (\w+)", r"\2 = computer.\1", code
                    )
                    code = re.sub(
                        r"from computer import (.+)",
                        lambda m: "\n".join(
                            f"{x.strip()} = computer.{x.strip()}"
                            for x in m.group(1).split(", ")
                        ),
                        code,
                    )
                    code = re.sub(r"import computer\.\w+\n", "pass\n", code)
                    # If it does this it sees the screenshot twice (which is expected jupyter behavior)
                    if any(
                        code.strip().split("\n")[-1].startswith(text)
                        for text in [
                            "computer.display.view",
                            "computer.display.screenshot",
                            "computer.view",
                            "computer.screenshot",
                        ]
                    ):
                        code = code + "\npass"

                # sync up some things (is this how we want to do this?)
                vulnera.computer.verbose = vulnera.verbose
                vulnera.computer.debug = vulnera.debug
                vulnera.computer.emit_images = vulnera.llm.supports_vision
                vulnera.computer.max_output = vulnera.max_output

                # sync up the vulnera's computer with your computer
                try:
                    if vulnera.sync_computer and language == "python":
                        computer_dict = vulnera.computer.to_dict()
                        if "_hashes" in computer_dict:
                            computer_dict.pop("_hashes")
                        if "system_message" in computer_dict:
                            computer_dict.pop("system_message")
                        computer_json = json.dumps(computer_dict)
                        sync_code = f"""import json\ncomputer.load_dict(json.loads('''{computer_json}'''))"""
                        vulnera.computer.run("python", sync_code)
                except Exception as e:
                    if vulnera.debug:
                        raise
                    print(str(e))
                    print("Failed to sync iComputer with your Computer. Continuing...")

                ## ↓ CODE IS RUN HERE

                for line in vulnera.computer.run(language, code, stream=True):
                    yield {"role": "computer", **line}

                ## ↑ CODE IS RUN HERE

                # sync up your computer with the vulnera's computer
                try:
                    if vulnera.sync_computer and language == "python":
                        # sync up the vulnera's computer with your computer
                        result = vulnera.computer.run(
                            "python",
                            """
                            import json
                            computer_dict = computer.to_dict()
                            if '_hashes' in computer_dict:
                                computer_dict.pop('_hashes')
                            if "system_message" in computer_dict:
                                computer_dict.pop("system_message")
                            print(json.dumps(computer_dict))
                            """,
                        )
                        result = result[-1]["content"]
                        vulnera.computer.load_dict(
                            json.loads(result.strip('"').strip("'"))
                        )
                except Exception as e:
                    if vulnera.debug:
                        raise
                    print(str(e))
                    print("Failed to sync your Computer with iComputer. Continuing.")

                # yield final "active_line" message, as if to say, no more code is running. unhighlight active lines
                # (is this a good idea? is this our responsibility? i think so — we're saying what line of code is running! ...?)
                yield {
                    "role": "computer",
                    "type": "console",
                    "format": "active_line",
                    "content": None,
                }

            except KeyboardInterrupt:
                break  # It's fine.
            except:
                yield {
                    "role": "computer",
                    "type": "console",
                    "format": "output",
                    "content": traceback.format_exc(),
                }

        else:
            ## LOOP MESSAGE
            # This makes it utter specific phrases if it doesn't want to be told to "Proceed."

            loop_message = vulnera.loop_message
            if vulnera.os:
                loop_message = loop_message.replace(
                    "If the entire task I asked for is done,",
                    "If the entire task I asked for is done, take a screenshot to verify it's complete, or if you've already taken a screenshot and verified it's complete,",
                )
            loop_breakers = vulnera.loop_breakers

            if (
                vulnera.loop
                and vulnera.messages
                and vulnera.messages[-1].get("role", "") == "assistant"
                and not any(
                    task_status in vulnera.messages[-1].get("content", "")
                    for task_status in loop_breakers
                )
            ):
                # Remove past loop_message messages
                vulnera.messages = [
                    message
                    for message in vulnera.messages
                    if message.get("content", "") != loop_message
                ]
                # Combine adjacent assistant messages, so hopefully it learns to just keep going!
                combined_messages = []
                for message in vulnera.messages:
                    if (
                        combined_messages
                        and message["role"] == "assistant"
                        and combined_messages[-1]["role"] == "assistant"
                        and message["type"] == "message"
                        and combined_messages[-1]["type"] == "message"
                    ):
                        combined_messages[-1]["content"] += "\n" + message["content"]
                    else:
                        combined_messages.append(message)
                vulnera.messages = combined_messages

                # Send model the loop_message:
                insert_loop_message = True

                continue

            # Doesn't want to run code. We're done!
            break

    return
