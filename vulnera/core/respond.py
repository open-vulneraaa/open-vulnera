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
    Enhanced with anti-hallucination mechanisms and improved autonomous execution.
    """

    last_unsupported_code = ""
    insert_loop_message = False
    failed_attempts = {}  # Track failed commands to prevent infinite loops
    max_retries_per_command = 3

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

        ## Rendering ↓
        rendered_system_message = render_message(vulnera, system_message)
        ## Rendering ↑

        rendered_system_message = {
            "role": "system",
            "type": "message",
            "content": rendered_system_message,
        }

        # If conversation state exists, include it in the system prompt for context continuity
        state_summary = vulnera.get_conversation_state_summary()
        if state_summary:
            rendered_system_message["content"] += "\n\nCURRENT CONVERSATION STATE:\n" + state_summary

        # Create the version of messages that we'll send to the LLM
        messages_for_llm = vulnera.messages.copy()
        messages_for_llm = [rendered_system_message] + messages_for_llm

        if insert_loop_message:
            messages_for_llm.append(
                {
                    "role": "user",
                    "type": "message",
                    "content": vulnera.loop_message,
                }
            )
            # Yield two newlines to separate the LLMs reply from previous messages
            yield {"role": "assistant", "type": "message", "content": "\n\n"}
            insert_loop_message = False

        ### RUN THE LLM ###

        assert (
            len(vulnera.messages) > 0
        ), "User message was not passed in. You need to pass in at least one message."

        if vulnera.messages[-1]["type"] != "code":
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
                    and ("auth" in error_message or "api key" in error_message)
                ):
                    output = traceback.format_exc()
                    raise Exception(
                        f"{output}\n\nThere might be an issue with your API key(s).\n\nTo reset your API key (we'll use OPENAI_API_KEY for this example, but you may need to reset your ANTHROPIC_API_KEY, etc):\n        Mac/Linux: 'export OPENAI_API_KEY=your-key-here',\n        Windows: 'setx OPENAI_API_KEY your-key-here' then restart terminal.\n\n"
                    )
                elif (
                    isinstance(e, litellm.exceptions.RateLimitError)
                    and ("exceeded" in str(e).lower() or "insufficient_quota" in str(e).lower())
                ):
                    display_markdown_message(
                        f""" > Rate limit or quota exceeded. Please check your API plan and billing details.
                        """
                    )
                    raise
                elif vulnera.offline == False and "not have access" in str(e).lower():
                    raise Exception(
                        f"The model '{vulnera.llm.model}' is invalid or you do not have access. Please verify the model name and your API credentials."
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

                # Normalize code block formatting
                if code.startswith("`\n"):
                    code = code[2:].strip()
                    if vulnera.verbose:
                        print("Removing `\n")
                    vulnera.messages[-1]["content"] = code

                # Track command in conversation state
                if "previous_commands" in vulnera.conversation_state:
                    vulnera.conversation_state["previous_commands"].append(code)

                # Hallucination 2: Double execute suffix
                if code.strip().endswith("executeexecute"):
                    code = code.replace("executeexecute", "")
                    vulnera.messages[-1]["content"] = code

                # Hallucination 3: JSON-formatted code block
                if code.replace("\n", "").replace(" ", "").startswith('{"language":'):
                    try:
                        code_dict = json.loads(code)
                        if set(code_dict.keys()) == {"language", "code"}:
                            language = code_dict["language"]
                            code = code_dict["code"]
                            vulnera.messages[-1]["content"] = code
                            vulnera.messages[-1]["format"] = language
                    except:
                        pass

                # Hallucination 4: Unquoted JSON keys
                if code.replace("\n", "").replace(" ", "").startswith("{language:"):
                    try:
                        code = code.replace("language: ", '"language": ').replace(
                            "code: ", '"code": '
                        )
                        code_dict = json.loads(code)
                        if set(code_dict.keys()) == {"language", "code"}:
                            language = code_dict["language"]
                            code = code_dict["code"]
                            vulnera.messages[-1]["content"] = code
                            vulnera.messages[-1]["format"] = language
                    except:
                        pass

                # Hallucination 5: functions.execute style wrappers
                if code.strip().startswith("functions.execute(") and code.strip().endswith(")"):
                    try:
                        payload = code.strip()[len("functions.execute("):-1].strip()
                        payload = payload.strip()
                        # Support JSON-like passing
                        if payload.endswith(","):
                            payload = payload[:-1]
                        if payload.startswith("{"):
                            parsed = json.loads(payload)
                            if "language" in parsed and "code" in parsed:
                                language = parsed.get("language", language)
                                code = parsed.get("code", code)
                                vulnera.messages[-1]["content"] = code
                                vulnera.messages[-1]["format"] = language
                    except Exception:
                        pass

                # Hallucination 5: Text/markdown code blocks that should be messages
                if language in ["text", "markdown", "plaintext"]:
                    real_content = vulnera.messages[-1]["content"]
                    vulnera.messages[-1] = {
                        "role": "assistant",
                        "type": "message",
                        "content": f"```\n{real_content}\n```",
                    }
                    continue

                # LOOP PREVENTION: Check if this exact command has failed multiple times
                code_hash = hash(code + language)
                if code_hash in failed_attempts:
                    if failed_attempts[code_hash] >= max_retries_per_command:
                        yield {
                            "role": "computer",
                            "type": "console",
                            "format": "output",
                            "content": f"ERROR: This command has failed {max_retries_per_command} times. Switching to alternative approach is required. Do not retry the same command.",
                        }
                        # Reset counter and break to force new approach
                        failed_attempts[code_hash] = 0
                        continue

                # ENVIRONMENT VALIDATION: Verify language is supported
                if vulnera.computer.terminal.get_language(language) is None:
                    output = f"`{language}` is not supported in this environment.\n\nAvailable languages: {', '.join([lang.name for lang in vulnera.computer.terminal.languages])}\n\nPlease use a supported language."

                    yield {
                        "role": "computer",
                        "type": "console",
                        "format": "output",
                        "content": output,
                    }

                    # Prevent infinite loop on unsupported language
                    if code != last_unsupported_code:
                        last_unsupported_code = code
                        continue
                    else:
                        break

                # VALIDATION: Check for empty code blocks
                if code.strip() == "":
                    yield {
                        "role": "computer",
                        "type": "console",
                        "format": "output",
                        "content": "ERROR: Code block is empty. You must provide actual code to execute.",
                    }
                    continue

                # Yield confirmation message for code execution
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
                    break

                # User may have edited the code - grab latest version
                code = [m for m in vulnera.messages if m["type"] == "code"][-1]["content"]

                # Computer API import handling (prevent duplicate imports)
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
                    
                    # Prevent double screenshot display
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

                # Sync settings with computer
                vulnera.computer.verbose = vulnera.verbose
                vulnera.computer.debug = vulnera.debug
                vulnera.computer.emit_images = vulnera.llm.supports_vision
                vulnera.computer.max_output = vulnera.max_output

                # Sync computer state (if enabled)
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
                    print("Failed to sync computer state. Continuing...")

                ## ↓ CODE EXECUTION HAPPENS HERE ↓

                execution_successful = True
                execution_output = []
                command_output = []

                # Adjust attack phase from code semantics
                if language == "shell" and re.search(r"\b(nmap|masscan|recon|enumeration)\b", code, re.I):
                    vulnera.conversation_state["attack_phase"] = "recon"
                elif language == "shell" and re.search(r"\b(sqlmap|sql injection|exploit|sqli|command injection)\b", code, re.I):
                    vulnera.conversation_state["attack_phase"] = "exploit"

                try:
                    for line in vulnera.computer.run(language, code, stream=True):
                        execution_output.append(line)
                        if line.get("format") == "output":
                            command_output.append(line.get("content", ""))
                        yield {"role": "computer", **line}
                        
                        # Check for error indicators in output
                        if line.get("format") == "output":
                            content = line.get("content", "").lower()
                            if any(err in content for err in ["error", "exception", "traceback", "failed", "not found"]):
                                execution_successful = False

                except Exception as exec_error:
                    execution_successful = False
                    yield {
                        "role": "computer",
                        "type": "console",
                        "format": "output",
                        "content": f"EXECUTION ERROR: {str(exec_error)}\n{traceback.format_exc()}",
                    }

                ## ↑ CODE EXECUTION COMPLETE ↑

                # Save command output to conversation state
                if "previous_outputs" in vulnera.conversation_state:
                    vulnera.conversation_state["previous_outputs"].append("".join(command_output))

                # Track failed attempts for loop prevention
                if not execution_successful:
                    if code_hash not in failed_attempts:
                        failed_attempts[code_hash] = 0
                    failed_attempts[code_hash] += 1
                else:
                    # Reset counter on success
                    if code_hash in failed_attempts:
                        failed_attempts[code_hash] = 0

                # Sync computer state back (if enabled)
                try:
                    if vulnera.sync_computer and language == "python":
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
                    print("Failed to sync computer state back. Continuing.")

                # Signal code execution complete
                yield {
                    "role": "computer",
                    "type": "console",
                    "format": "active_line",
                    "content": None,
                }

            except KeyboardInterrupt:
                # Stop any running computer operations
                try:
                    vulnera.computer.stop()
                except:
                    pass  # Ignore errors during emergency stop
                break
            except Exception as e:
                yield {
                    "role": "computer",
                    "type": "console",
                    "format": "output",
                    "content": f"CRITICAL ERROR:\n{traceback.format_exc()}",
                }
                # Track critical errors
                code_hash = hash(code + language)
                if code_hash not in failed_attempts:
                    failed_attempts[code_hash] = 0
                failed_attempts[code_hash] += 1

        else:
            ## AUTONOMOUS LOOP MESSAGE HANDLING

            loop_message = vulnera.loop_message
            
            # OS mode enhancement
            if vulnera.os:
                loop_message = loop_message.replace(
                    "If the entire task I asked for is done,",
                    "If the entire task I asked for is done, take a screenshot to verify it's complete, or if you've already taken a screenshot and verified it's complete,",
                )
            
            loop_breakers = vulnera.loop_breakers

            # Determine if we should continue looping
            if (
                vulnera.loop
                and vulnera.messages
                and vulnera.messages[-1].get("role", "") == "assistant"
                and not any(
                    task_status in vulnera.messages[-1].get("content", "")
                    for task_status in loop_breakers
                )
            ):
                # Remove past loop messages to avoid clutter
                vulnera.messages = [
                    message
                    for message in vulnera.messages
                    if message.get("content", "") != loop_message
                ]
                
                # Combine adjacent assistant messages for continuity
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

                # Insert loop continuation message
                insert_loop_message = True
                continue

            # Task complete or loop breaker encountered
            break

    return
