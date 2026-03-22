import sys

if "--os" in sys.argv:
    from rich import print as rich_print
    from rich.markdown import Markdown
    from rich.rule import Rule

    def print_markdown(message):
        """
        Display markdown message. Works with multiline strings with lots of indentation.
        Will automatically make single line > tags beautiful.
        """

        for line in message.split("\n"):
            line = line.strip()
            if line == "":
                print("")
            elif line == "---":
                rich_print(Rule(style="white"))
            else:
                try:
                    rich_print(Markdown(line))
                except UnicodeEncodeError as e:
                    # Replace the problematic character or handle the error as needed
                    print("Error displaying line:", line)

        if "\n" not in message and message.startswith(">"):
            # Aesthetic choice. For these tags, they need a space below them
            print("")

    from importlib.metadata import version
    import requests
    from packaging import version

    def check_for_update():
        # Fetch the latest version from the PyPI API
        response = requests.get(f"https://pypi.org/pypi/open-vulnera/json")
        latest_version = response.json()["info"]["version"]

        # Get the current version using importlib.metadata
        current_version = version("open-vulnera")

        return version.parse(latest_version) > version.parse(current_version)

    if check_for_update():
        print_markdown(
            "> **A new version of Open Vulnera is available.**\n>Please run: `pip install --upgrade open-vulnera`\n\n---"
        )

    if "--voice" in sys.argv:
        print("Coming soon...")
    from .computer_use.loop import run_async_main

    run_async_main()
    exit()

try:
    from .core.async_core import AsyncVulnera
    from .core.computer.terminal.base_language import BaseLanguage
    from .core.core import OpenVulnera
except Exception:
    AsyncVulnera = None
    BaseLanguage = None
    OpenVulnera = None

# Lazy-initialized globals to avoid import-time side effects (network calls, etc.)
vulnera = None
computer = None

def init_vulnera():
    """Initialize and return the global `vulnera` instance.

    Use this to create the runtime instance when needed instead of at import time.
    """
    global vulnera, computer
    if vulnera is None:
        if OpenVulnera is None:
            raise RuntimeError("OpenVulnera class is unavailable")
        vulnera = OpenVulnera()
        computer = vulnera.computer
    return vulnera

#     ____                      ____      __                            __
#    / __ \____  ___  ____     /  _/___  / /____  _________  ________  / /____  _____
#   / / / / __ \/ _ \/ __ \    / // __ \/ __/ _ \/ ___/ __ \/ ___/ _ \/ __/ _ \/ ___/
#  / /_/ / /_/ /  __/ / / /  _/ // / / / /_/  __/ /  / /_/ / /  /  __/ /_/  __/ /
#  \____/ .___/\___/_/ /_/  /___/_/ /_/\__/\___/_/  / .___/_/   \___/\__/\___/_/
#      /_/                                         /_/
