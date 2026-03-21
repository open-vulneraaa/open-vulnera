import argparse
import os
import sys
import time

from importlib.metadata import version, PackageNotFoundError

from vulnera.terminal_interface.contributing_conversations import (
    contribute_conversation_launch_logic,
    contribute_conversations,
)

from .conversation_navigator import conversation_navigator
from .profiles.profiles import open_storage_dir, profile, reset_profile
from .utils.check_for_update import check_for_update
from .validate_llm_settings import validate_llm_settings


def start_terminal_interface(vulnera):
    """
    Meant to be used from the command line. Parses arguments, starts Vulnera's terminal interface.
    
    This function validates the vulnera instance and its attributes before attempting to use them.
    """
    
    # Validate input
    if vulnera is None:
        raise ValueError("vulnera instance cannot be None")
    
    if not hasattr(vulnera, 'llm') or vulnera.llm is None:
        raise ValueError("vulnera.llm is missing or None - LLM not properly initialized")
    
    if not hasattr(vulnera, 'computer') or vulnera.computer is None:
        raise ValueError("vulnera.computer is missing or None - Computer interface not properly initialized")

    # Instead use an async vulnera, which has a server. Set settings on that
    if "--server" in sys.argv:
        from vulnera import AsyncInterpreter

        try:
            vulnera = AsyncInterpreter()
            if vulnera is None:
                raise ValueError("AsyncInterpreter initialization returned None")
            if not hasattr(vulnera, 'llm') or vulnera.llm is None:
                raise ValueError("AsyncInterpreter.llm is missing or None")
            if not hasattr(vulnera, 'computer') or vulnera.computer is None:
                raise ValueError("AsyncInterpreter.computer is missing or None")
        except Exception as e:
            print(f"ERROR: Failed to initialize AsyncInterpreter for --server mode: {e}", file=sys.stderr)
            raise

    arguments = [
        {
            "name": "profile",
            "nickname": "p",
            "help_text": "name of profile. run `--profiles` to open profile directory",
            "type": str,
            "default": "default.yaml",
        },
        {
            "name": "custom_instructions",
            "nickname": "ci",
            "help_text": "custom instructions for the language model. will be appended to the system_message",
            "type": str,
            "attribute": {"object": vulnera, "attr_name": "custom_instructions"},
        },
        {
            "name": "system_message",
            "nickname": "sm",
            "help_text": "(we don't recommend changing this) base prompt for the language model",
            "type": str,
            "attribute": {"object": vulnera, "attr_name": "system_message"},
        },
        {
            "name": "auto_run",
            "nickname": "y",
            "help_text": "automatically run generated code",
            "type": bool,
            "attribute": {"object": vulnera, "attr_name": "auto_run"},
        },
        {
            "name": "no_highlight_active_line",
            "nickname": "nhl",
            "help_text": "turn off active line highlighting in code blocks",
            "type": bool,
            "action": "store_true",
            "default": False,  # Default to False, meaning highlighting is on by default
        },
        {
            "name": "verbose",
            "nickname": "v",
            "help_text": "print detailed logs",
            "type": bool,
            "attribute": {"object": vulnera, "attr_name": "verbose"},
        },
        {
            "name": "model",
            "nickname": "m",
            "help_text": "language model to use",
            "type": str,
            "attribute": {"object": vulnera.llm, "attr_name": "model"},
        },
        {
            "name": "temperature",
            "nickname": "t",
            "help_text": "optional temperature setting for the language model",
            "type": float,
            "attribute": {"object": vulnera.llm, "attr_name": "temperature"},
        },
        {
            "name": "llm_supports_vision",
            "nickname": "lsv",
            "help_text": "inform Vulnera that your model supports vision, and can receive vision inputs",
            "type": bool,
            "action": argparse.BooleanOptionalAction,
            "attribute": {"object": vulnera.llm, "attr_name": "supports_vision"},
        },
        {
            "name": "llm_supports_functions",
            "nickname": "lsf",
            "help_text": "inform Vulnera that your model supports OpenAI-style functions, and can make function calls",
            "type": bool,
            "action": argparse.BooleanOptionalAction,
            "attribute": {"object": vulnera.llm, "attr_name": "supports_functions"},
        },
        {
            "name": "context_window",
            "nickname": "cw",
            "help_text": "optional context window size for the language model",
            "type": int,
            "attribute": {"object": vulnera.llm, "attr_name": "context_window"},
        },
        {
            "name": "max_tokens",
            "nickname": "x",
            "help_text": "optional maximum number of tokens for the language model",
            "type": int,
            "attribute": {"object": vulnera.llm, "attr_name": "max_tokens"},
        },
        {
            "name": "max_budget",
            "nickname": "b",
            "help_text": "optionally set the max budget (in USD) for your llm calls",
            "type": float,
            "attribute": {"object": vulnera.llm, "attr_name": "max_budget"},
        },
        {
            "name": "api_base",
            "nickname": "ab",
            "help_text": "optionally set the API base URL for your llm calls (this will override environment variables)",
            "type": str,
            "attribute": {"object": vulnera.llm, "attr_name": "api_base"},
        },
        {
            "name": "api_key",
            "nickname": "ak",
            "help_text": "optionally set the API key for your llm calls (this will override environment variables)",
            "type": str,
            "attribute": {"object": vulnera.llm, "attr_name": "api_key"},
        },
        {
            "name": "api_version",
            "nickname": "av",
            "help_text": "optionally set the API version for your llm calls (this will override environment variables)",
            "type": str,
            "attribute": {"object": vulnera.llm, "attr_name": "api_version"},
        },
        {
            "name": "max_output",
            "nickname": "xo",
            "help_text": "optional maximum number of characters for code outputs",
            "type": int,
            "attribute": {"object": vulnera, "attr_name": "max_output"},
        },
        {
            "name": "loop",
            "help_text": "runs Vulnera in a loop, requiring it to admit to completing/failing task",
            "type": bool,
            "attribute": {"object": vulnera, "attr_name": "loop"},
        },
        {
            "name": "disable_telemetry",
            "nickname": "dt",
            "help_text": "disables sending of basic anonymous usage stats",
            "type": bool,
            "default": False,
            "attribute": {"object": vulnera, "attr_name": "disable_telemetry"},
        },
        {
            "name": "offline",
            "nickname": "o",
            "help_text": "turns off all online features (except the language model, if it's hosted)",
            "type": bool,
            "attribute": {"object": vulnera, "attr_name": "offline"},
        },
        {
            "name": "speak_messages",
            "nickname": "sp",
            "help_text": "(Mac only, experimental) use the applescript `say` command to read messages aloud",
            "type": bool,
            "attribute": {"object": vulnera, "attr_name": "speak_messages"},
        },
        {
            "name": "safe_mode",
            "nickname": "safe",
            "help_text": "optionally enable safety mechanisms like code scanning; valid options are off, ask, and auto",
            "type": str,
            "choices": ["off", "ask", "auto"],
            "default": "off",
            "attribute": {"object": vulnera, "attr_name": "safe_mode"},
        },
        {
            "name": "debug",
            "nickname": "debug",
            "help_text": "debug mode for open vulnera developers",
            "type": bool,
            "attribute": {"object": vulnera, "attr_name": "debug"},
        },
        {
            "name": "fast",
            "nickname": "f",
            "help_text": "runs `vulnera --model gpt-4o-mini` and asks Vulnera to be extremely concise (shortcut for `vulnera --profile fast`)",
            "type": bool,
        },
        {
            "name": "multi_line",
            "nickname": "ml",
            "help_text": "enable multi-line inputs starting and ending with ```",
            "type": bool,
            "attribute": {"object": vulnera, "attr_name": "multi_line"},
        },
        {
            "name": "local",
            "nickname": "l",
            "help_text": "setup a local model (shortcut for `vulnera --profile local`)",
            "type": bool,
        },
        {
            "name": "codestral",
            "help_text": "shortcut for `vulnera --profile codestral`",
            "type": bool,
        },
        {
            "name": "assistant",
            "help_text": "shortcut for `vulnera --profile assistant.py`",
            "type": bool,
        },
        {
            "name": "llama3",
            "help_text": "shortcut for `vulnera --profile llama3`",
            "type": bool,
        },
        {
            "name": "groq",
            "help_text": "shortcut for `vulnera --profile groq`",
            "type": bool,
        },
        {
            "name": "vision",
            "nickname": "vi",
            "help_text": "experimentally use vision for supported languages (shortcut for `vulnera --profile vision`)",
            "type": bool,
        },
        {
            "name": "os",
            "nickname": "os",
            "help_text": "experimentally let Open Vulnera control your mouse and keyboard (shortcut for `vulnera --profile os`)",
            "type": bool,
        },
        # Special.commands
        {
            "name": "reset_profile",
            "help_text": "reset a profile file. run `--reset_profile` without an argument to reset all default profiles",
            "type": str,
            "default": "NOT_PROVIDED",
            "nargs": "?",  # This means you can pass in nothing if you want
        },
        {"name": "profiles", "help_text": "opens profiles directory", "type": bool},
        {
            "name": "local_models",
            "help_text": "opens local models directory",
            "type": bool,
        },
        {
            "name": "conversations",
            "help_text": "list conversations to resume",
            "type": bool,
        },
        {
            "name": "server",
            "help_text": "start open vulnera as a server",
            "type": bool,
        },
        {
            "name": "version",
            "help_text": "get Open Vulnera's version number",
            "type": bool,
        },
        {
            "name": "contribute_conversation",
            "help_text": "let Open Vulnera use the current conversation to train an Open-Source LLM",
            "type": bool,
            "attribute": {
                "object": vulnera,
                "attr_name": "contribute_conversation",
            },
        },
        {
            "name": "plain",
            "nickname": "pl",
            "help_text": "set output to plain text",
            "type": bool,
            "attribute": {
                "object": vulnera,
                "attr_name": "plain_text_display",
            },
        },
        {
            "name": "stdin",
            "nickname": "s",
            "help_text": "Run Vulnera in stdin mode",
            "type": bool,
        },
    ]

    if "--stdin" in sys.argv and "--plain" not in sys.argv:
        sys.argv += ["--plain"]

    # i shortcut
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        message = " ".join(sys.argv[1:])
        vulnera.messages.append(
            {"role": "user", "type": "message", "content": "I " + message}
        )
        sys.argv = sys.argv[:1]

        vulnera.custom_instructions = "UPDATED INSTRUCTIONS: You are in ULTRA FAST, ULTRA CERTAIN mode. Do not ask the user any questions or run code to gathet information. Go as quickly as you can. Run code quickly. Do not plan out loud, simply start doing the best thing. The user expects speed. Trust that the user knows best. Just interpret their ambiguous.command as quickly and certainly as possible and try to fulfill it IN ONE COMMAND, assuming they have the right information. If they tell you do to something, just do it quickly in one.command, DO NOT try to get more information (for example by running `cat` to get a file's infomration— this is probably unecessary!). DIRECTLY DO THINGS AS FAST AS POSSIBLE."

        files_in_directory = os.listdir()[:100]
        vulnera.custom_instructions += (
            "\nThe files in CWD, which THE USER MAY BE REFERRING TO, are: "
            + ", ".join(files_in_directory)
        )

        # vulnera.debug = True

    # Check for deprecated flags before parsing arguments
    deprecated_flags = {
        "--debug_mode": "--verbose",
    }

    for old_flag, new_flag in deprecated_flags.items():
        if old_flag in sys.argv:
            print(f"\n`{old_flag}` has been renamed to `{new_flag}`.\n")
            time.sleep(1.5)
            sys.argv.remove(old_flag)
            sys.argv.append(new_flag)

    class CustomHelpParser(argparse.ArgumentParser):
        def print_help(self, *args, **kwargs):
            super().print_help(*args, **kwargs)
            special_help_message = '''
Open Vulnera, 2026

Use """ to write multi-line messages.
            '''
            print(special_help_message)

    parser = CustomHelpParser(
        description="Open Vulnera", usage="%(prog)s [options]"
    )

    # Add arguments
    for arg in arguments:
        default = arg.get("default")
        action = arg.get("action", "store_true")
        nickname = arg.get("nickname")

        name_or_flags = [f'--{arg["name"]}']
        if nickname:
            name_or_flags.append(f"-{nickname}")

        # Construct argument name flags
        flags = (
            [f"-{nickname}", f'--{arg["name"]}'] if nickname else [f'--{arg["name"]}']
        )

        if arg["type"] == bool:
            parser.add_argument(
                *flags,
                dest=arg["name"],
                help=arg["help_text"],
                action=action,
                default=default,
            )
        else:
            choices = arg.get("choices")
            parser.add_argument(
                *flags,
                dest=arg["name"],
                help=arg["help_text"],
                type=arg["type"],
                choices=choices,
                default=default,
                nargs=arg.get("nargs"),
            )

    # Add positional argument for message
    parser.add_argument('message', nargs='*', help='The message to send to the AI')

    args = parser.parse_args()

    if args.profiles:
        open_storage_dir("profiles")
        return

    if args.local_models:
        open_storage_dir("models")
        return

    if args.reset_profile is not None and args.reset_profile != "NOT_PROVIDED":
        reset_profile(
            args.reset_profile
        )  # This will be None if they just ran `--reset_profile`
        return

    if args.version:
        ov_version = version("open-vulnera")
        update_name = "Developer Preview"  # Change this with each major update
        print(f"Open Vulnera {ov_version} {update_name}")
        return

    if args.no_highlight_active_line:
        if hasattr(vulnera, 'highlight_active_line'):
            vulnera.highlight_active_line = False
        else:
            print("WARNING: highlight_active_line attribute not found on vulnera object", file=sys.stderr)

    # if safe_mode and auto_run are enabled, safe_mode disables auto_run
    try:
        auto_run = getattr(vulnera, 'auto_run', False)
        safe_mode = getattr(vulnera, 'safe_mode', 'off')
        
        if auto_run and (safe_mode == "ask" or safe_mode == "auto"):
            setattr(vulnera, "auto_run", False)
    except Exception as e:
        print(f"WARNING: Error checking auto_run/safe_mode settings: {e}", file=sys.stderr)

    ### Set attributes on vulnera, so that a profile script can read the arguments passed in via the CLI

    set_attributes(args, arguments)

    ### Apply profile

    # Profile shortcuts, which should probably not exist:

    if args.fast:
        args.profile = "fast.yaml"

    if args.vision:
        args.profile = "vision.yaml"

    if args.os:
        args.profile = "os.py"

    if args.local:
        args.profile = "local.py"
        if args.vision:
            # This is local vision, set up moondream!
            try:
                if vulnera and hasattr(vulnera, 'computer') and vulnera.computer:
                    if hasattr(vulnera.computer, 'vision') and vulnera.computer.vision:
                        vulnera.computer.vision.load()
                    else:
                        print("WARNING: vision module not available in computer interface", file=sys.stderr)
                else:
                    print("WARNING: computer interface not available for vision setup", file=sys.stderr)
            except Exception as e:
                print(f"WARNING: Failed to load vision module: {e}", file=sys.stderr)
        if args.os:
            args.profile = "local-os.py"

    if args.codestral:
        args.profile = "codestral.py"
        if args.vision:
            args.profile = "codestral-vision.py"
        if args.os:
            args.profile = "codestral-os.py"

    if args.assistant:
        args.profile = "assistant.py"

    if args.llama3:
        args.profile = "llama3.py"
        if args.vision:
            args.profile = "llama3-vision.py"
        if args.os:
            args.profile = "llama3-os.py"

    if args.groq:
        args.profile = "groq.py"

    # Apply profile and validate result
    try:
        new_vulnera = profile(
            vulnera,
            args.profile or get_argument_dictionary(arguments, "profile")["default"],
        )
        
        if new_vulnera is None:
            raise ValueError("profile() returned None")
        
        vulnera = new_vulnera
        
        # Re-validate after profile application
        if not hasattr(vulnera, 'llm') or vulnera.llm is None:
            raise ValueError("After applying profile, vulnera.llm is missing or None")
        if not hasattr(vulnera, 'computer') or vulnera.computer is None:
            raise ValueError("After applying profile, vulnera.computer is missing or None")
            
    except Exception as e:
        print(f"ERROR: Failed to apply profile '{args.profile or 'default.yaml'}': {e}", file=sys.stderr)
        raise
    ### Set attributes on vulnera, because the arguments passed in via the CLI should override profile

    set_attributes(args, arguments)
    
    # Set disable_telemetry with proper error handling
    try:
        vulnera.disable_telemetry = (
            os.getenv("DISABLE_TELEMETRY", "false").lower() == "true"
            or args.disable_telemetry
        )
    except Exception as e:
        print(f"WARNING: Could not set disable_telemetry: {e}", file=sys.stderr)

    ### Set some helpful settings we know are likely to be true

    # Verify model is set before trying to configure it
    try:
        model_name = getattr(vulnera.llm, 'model', None)
        
        if model_name is None:
            print("WARNING: Model name not set. Skipping model-specific configuration.", file=sys.stderr)
        else:
            if model_name == "gpt-4" or model_name == "openai/gpt-4":
                if vulnera.llm.context_window is None:
                    vulnera.llm.context_window = 6500
                if vulnera.llm.max_tokens is None:
                    vulnera.llm.max_tokens = 4096
                if vulnera.llm.supports_functions is None:
                    vulnera.llm.supports_functions = (
                        False if "vision" in model_name else True
                    )

            elif model_name.startswith("gpt-4") or model_name.startswith("openai/gpt-4"):
                if vulnera.llm.context_window is None:
                    vulnera.llm.context_window = 123000
                if vulnera.llm.max_tokens is None:
                    vulnera.llm.max_tokens = 4096
                if vulnera.llm.supports_functions is None:
                    vulnera.llm.supports_functions = (
                        False if "vision" in model_name else True
                    )

            if model_name.startswith("gpt-3.5-turbo") or model_name.startswith("openai/gpt-3.5-turbo"):
                if vulnera.llm.context_window is None:
                    vulnera.llm.context_window = 16000
                if vulnera.llm.max_tokens is None:
                    vulnera.llm.max_tokens = 4096
                if vulnera.llm.supports_functions is None:
                    vulnera.llm.supports_functions = True
    except Exception as e:
        print(f"WARNING: Error configuring model settings: {e}", file=sys.stderr)

    ### Check for update

    try:
        if not vulnera.offline and not args.stdin:
            # This message should actually be pushed into the utility
            if check_for_update():
                vulnera.display_message(
                    "> **A new version of Open Vulnera is available.**\n>Please run: `pip install --upgrade open-vulnera`\n\n---"
                )
    except:
        # Doesn't matter
        pass

    if vulnera.llm.api_base:
        try:
            model_name = getattr(vulnera.llm, 'model', None)
            
            if model_name is None:
                print("WARNING: Cannot apply api_base prefix - model is None", file=sys.stderr)
            elif (
                not model_name.lower().startswith("openai/")
                and not model_name.lower().startswith("azure/")
                and not model_name.lower().startswith("ollama")
                and not model_name.lower().startswith("jan")
                and not model_name.lower().startswith("local")
            ):
                vulnera.llm.model = "openai/" + model_name
            elif model_name.lower().startswith("jan/"):
                # Strip jan/ from the model name
                vulnera.llm.model = model_name[4:]
        except Exception as e:
            print(f"WARNING: Error applying api_base configuration: {e}", file=sys.stderr)

    # If --conversations is used, run conversation_navigator
    if args.conversations:
        conversation_navigator(vulnera)
        return

    # Handle model name aliases
    try:
        if vulnera.llm.model in [
            "claude-3.5",
            "claude-3-5",
            "claude-3.5-sonnet",
            "claude-3-5-sonnet",
        ]:
            vulnera.llm.model = "claude-3-5-sonnet-20240620"
    except Exception as e:
        print(f"WARNING: Error handling model name aliases: {e}", file=sys.stderr)

    if not args.server:
        # This SHOULD RUN WHEN THE SERVER STARTS. But it can't rn because
        # if you don't have an API key, a prompt shows up, breaking the whole thing.
        try:
            validate_llm_settings(vulnera)
        except Exception as e:
            print(f"ERROR: LLM validation failed: {e}", file=sys.stderr)
            raise

    if args.server:
        try:
            if not hasattr(vulnera, 'server') or vulnera.server is None:
                raise ValueError("Server not available - vulnera.server is None")
            vulnera.server.run()
        except Exception as e:
            print(f"ERROR: Failed to start server: {e}", file=sys.stderr)
            raise
        return

    try:
        vulnera.in_terminal_interface = True
    except Exception as e:
        print(f"WARNING: Could not set in_terminal_interface: {e}", file=sys.stderr)

    try:
        contribute_conversation_launch_logic(vulnera)
    except Exception as e:
        print(f"ERROR: Failed to process conversation logic: {e}", file=sys.stderr)
        raise

    # Standard in mode
    try:
        if args.stdin:
            stdin_input = input()
            vulnera.plain_text_display = True
            vulnera.chat(stdin_input)
        elif args.message:
            message = " ".join(args.message)
            vulnera.chat(message)
        else:
            vulnera.chat()
    except Exception as e:
        print(f"ERROR: Chat session failed: {e}", file=sys.stderr)
        raise


def set_attributes(args, arguments):
    """Set attributes on the vulnera object based on parsed command-line arguments.
    
    This function includes validation to ensure attributes exist before setting them.
    """
    for argument_name, argument_value in vars(args).items():
        if argument_value is not None:
            if argument_dictionary := get_argument_dictionary(arguments, argument_name):
                if "attribute" in argument_dictionary:
                    attr_dict = argument_dictionary["attribute"]
                    target_object = attr_dict["object"]
                    attr_name = attr_dict["attr_name"]
                    
                    # Validate target object exists
                    if target_object is None:
                        print(
                            f"WARNING: Cannot set attribute '{attr_name}' - target object is None",
                            file=sys.stderr
                        )
                        continue
                    
                    # Validate attribute can be set
                    try:
                        setattr(target_object, attr_name, argument_value)
                        
                        if args.verbose:
                            print(
                                f"Setting attribute {attr_name} on {target_object.__class__.__name__.lower()} to '{argument_value}'..."
                            )
                    except AttributeError as e:
                        print(
                            f"WARNING: Failed to set attribute '{attr_name}' on {target_object.__class__.__name__}: {e}",
                            file=sys.stderr
                        )
                    except Exception as e:
                        print(
                            f"ERROR: Unexpected error setting attribute '{attr_name}': {e}",
                            file=sys.stderr
                        )


def get_argument_dictionary(arguments: list[dict], key: str) -> dict:
    if (
        len(
            argument_dictionary_list := list(
                filter(lambda x: x["name"] == key, arguments)
            )
        )
        > 0
    ):
        return argument_dictionary_list[0]
    return {}


def main():
    """Main entry point for the terminal interface.
    
    This function initializes the OpenVulnera instance and starts the terminal interface,
    with comprehensive error handling and validation.
    """
    vulnera = None
    
    try:
        # Initialize the OpenVulnera instance
        from vulnera import init_vulnera
        
        try:
            vulnera = init_vulnera()
        except Exception as e:
            print(f"FATAL ERROR: Failed to initialize OpenVulnera: {e}", file=sys.stderr)
            print("\nDebugging info:", file=sys.stderr)
            print(f"  Error type: {type(e).__name__}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return 1
        
        # Validate that vulnera instance was created successfully
        if vulnera is None:
            print("FATAL ERROR: OpenVulnera initialization failed - instance is None", file=sys.stderr)
            return 1
        
        # Validate required attributes exist
        if not hasattr(vulnera, 'llm') or vulnera.llm is None:
            print("FATAL ERROR: OpenVulnera initialization failed - llm attribute is missing or None", file=sys.stderr)
            return 1
        
        if not hasattr(vulnera, 'computer') or vulnera.computer is None:
            print("FATAL ERROR: OpenVulnera initialization failed - computer attribute is missing or None", file=sys.stderr)
            return 1
        
        # Start the terminal interface
        start_terminal_interface(vulnera)
        
    except KeyboardInterrupt:
        print("\n\nKeyboard interrupt received.", file=sys.stderr)
        try:
            if vulnera is not None and hasattr(vulnera, 'computer') and vulnera.computer is not None:
                vulnera.computer.terminate()

                if (not vulnera.offline and not vulnera.disable_telemetry):
                    # Quick feedback flow: if user opted into contributing, forward messages (no prompts).
                    if vulnera.contribute_conversation and vulnera.messages != []:
                        conversation_id = (
                            vulnera.conversation_id
                            if hasattr(vulnera, "conversation_id")
                            else None
                        )
                        contribute_conversations(
                            [vulnera.messages], None, conversation_id
                        )

        except KeyboardInterrupt:
            pass
        except Exception as cleanup_error:
            print(f"Error during cleanup: {cleanup_error}", file=sys.stderr)
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        try:
            if vulnera is not None and hasattr(vulnera, 'computer') and vulnera.computer is not None:
                vulnera.computer.terminate()
        except Exception as cleanup_error:
            print(f"Error during cleanup: {cleanup_error}", file=sys.stderr)
        return 1
    finally:
        # Ensure proper cleanup regardless of how we exit
        if vulnera is not None and hasattr(vulnera, 'computer') and vulnera.computer is not None:
            try:
                vulnera.computer.terminate()
            except Exception as cleanup_error:
                print(f"Error during final cleanup: {cleanup_error}", file=sys.stderr)
