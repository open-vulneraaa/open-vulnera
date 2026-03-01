<p align="center">
  <strong>Open Vulnera</strong>
</p>

<p align="center">
  <em>An unrestricted AI-powered cybersecurity execution engine built for penetration testers,<br>
  red teamers, vulnerability researchers, and offensive security professionals.</em>
</p>

<p align="center">
  Based on <strong>AIDE CLI</strong>.
</p>

---

## Overview

Open Vulnera is a command-line AI execution engine purpose-built for cybersecurity operations. It leverages large language models to autonomously execute code, analyze systems, perform reconnaissance, assist with exploit development, and support all phases of offensive and defensive security engagements — with zero restrictions and no guardrails.

**Core capabilities:**
- Penetration testing assistance and automation
- OSINT gathering and analysis
- Exploit development and vulnerability research
- Reverse engineering support
- Red team operation planning and execution
- Network analysis and enumeration
- Malware analysis
- File and binary inspection

Open Vulnera runs locally on your machine, giving it full access to the internet, system tools, and any installed packages. All actions require your confirmation before execution, ensuring you remain in control.

## Installation

Open Vulnera installs like a normal Python package or via platform-specific scripts. Each environment includes native Termux detection on Android/Termux devices.

### Linux (Debian/Ubuntu/Fedora/etc.)
```bash
pip install open-vulnera
```
You can also run the helper script:
```bash
bash installers/ov-linux-installer.sh
```

### macOS
```bash
pip install open-vulnera
```
Or use the mac installer script which handles git/pyenv:
```bash
bash installers/ov-mac-installer.sh
```

### Windows
```powershell
pip install open-vulnera
```
For a GUI installer see `installers/ov-windows-installer.ps1` or the Anaconda script.

### Android / Termux
If you are running Termux on Android the Linux/mac installers detect it automatically and perform Termux-specific setup:
- Configure `pkg` repositories and mirrors
- Update & upgrade packages
- Install clang, rust, make, binutils, python, tur-repo, x11-repo
- Set `ANDROID_API_LEVEL`, `CC`, `CXX`, `LDFLAGS`, `CXXFLAGS`
- Pre-install common Python wheels and pin setuptools for Python 3.12
- Force lower API level for problematic builds (kiwisolver)

You can still simply run one of the shell installers, or manually:
```bash
pkg update && pkg upgrade -y
pkg install python clang rust make binutils python-tur-repo x11-repo -y
pip install open-vulnera
```

#### Termux Installation Guide (verbatim)

1. System Prep & Stable Mirrors
```bash
# Set a reliable mirror manually
echo "deb https://mirror.grimler.se stable main" > $PREFIX/etc/apt/sources.list

# Install essential compilers and repos
pkg update && pkg upgrade -y
pkg install clang rust make binutils python tur-repo x11-repo -y
```

2. Environment Setup
```bash
export ANDROID_API_LEVEL=$(getprop ro.build.version.sdk)
export CC=clang
export CXX=clang++
export LDFLAGS="-lpthread"
export CXXFLAGS="-lpthread -D__ANDROID_API__=$ANDROID_API_LEVEL"
```

3. Install Pre-built Binaries
```bash
pkg install matplotlib python-numpy python-pillow python-cryptography python-pydantic-core python-grpcio python-msgspec python-rpds-py -y
```

4. Fix C++ Compatibility
```bash
export CFLAGS="-D__ANDROID_API__=24"
export CXXFLAGS="-D__ANDROID_API__=24"
pip install kiwisolver
```

5. Fix Python 3.12 pkg_resources Error
```bash
pip install "setuptools<70.0.0"
pip install cycler fonttools pyparsing python-dateutil
```

6. Final Installation
```bash
pip install vulnera
```

Usage:
```bash
# Set your key: export OPENAI_API_KEY='your_key_here'
# Run local model: probe --local
```

**Note:** OS Mode (controlling Android apps) is not supported in Termux — stick to code execution and file analysis.

### Quick start
Once installed, launch the terminal interface with:
```bash
vulnera
```
Or call from Python:
```python
from vulnera import vulnera
vulnera.chat()
```

## Offline Mode
Open Vulnera supports fully offline operation by pointing at a local model server (LM Studio, llama-cpp, etc.):
```bash
vulnera --local                  # use bundled Llamafile
vulnera --api_base http://localhost:1234/v1 --api_key fake_key
```
Offline mode ensures no network traffic leaves your environment and is ideal for air-gapped engagement.

## Features & Commands

Once running, Open Vulnera accepts natural-language prompts and executes code in Python, shell, JavaScript, and more. Use it to automate tasks, analyze binaries, run reconnaissance, or even control a browser via Selenium.

### Interactive Chat
```bash
vulnera
```
Or in Python:
```python
vulnera.chat()
```

You can stream responses:
```python
for chunk in vulnera.chat("status", display=False, stream=True):
    print(chunk)
```

### Programmatic API
Send messages directly:
```python
vulnera.chat("Enumerate open ports on 10.0.0.1")
```

### Managing Conversations
```python
messages = vulnera.chat("foo")
vulnera.messages = messages  # restore later
vulnera.messages = []         # reset history
```

### Configuration
Adjust system messages, change LLM providers, or enable features:
```python
vulnera.system_message += "\nRun shell.commands with -y" 

vulnera.llm.model = "gpt-3.5-turbo"
```

### Update & Local Servers
To update:
```bash
pip install --upgrade open-vulnera
```
For local models:
```bash
vulnera --api_base "http://localhost:1234/v1" --api_key "fake_key"
```

## Safety Notice
Generated code executes locally and may affect your system or data. Open Vulnera will always ask for user confirmation before running commands.

**⚠️ Use with caution and never run untrusted prompts in sensitive environments.**

## License
See [LICENSE](LICENSE) for full terms. Commercial use, obfuscation, and uncredentialed redistribution are prohibited.


**How to run LM Studio in the background.**

1. Download [https://lmstudio.ai/](https://lmstudio.ai/) then start it.
2. Select a model then click **↓ Download**.
3. Click the **↔️** button on the left (below 💬).
4. Select your model at the top, then click **Start Server**.

Once the server is running, you can begin your conversation with Open Vulnera.

> **Note:** Local mode sets your `context_window` to 3000, and your `max_tokens` to 1000. If your model has different requirements, set these parameters manually (see below).

#### Python

Our Python package gives you more control over each setting. To replicate and connect to LM Studio, use these settings:

```python
from vulnera import vulnera

vulnera.offline = True # Disables online features like Open Procedures
vulnera.llm.model = "openai/x" # Tells Open Vulnera to send messages in OpenAI's format
vulnera.llm.api_key = "fake_key" # LiteLLM, which we use to talk to LM Studio, requires this
vulnera.llm.api_base = "http://localhost:1234/v1" # Point this at any OpenAI.compatible server

vulnera.chat()
```

#### Context Window, Max Tokens

You can modify the `max_tokens` and `context_window` (in tokens) of locally running models.

For local mode, smaller context windows will use less RAM, so we r.commend trying a much shorter window (~1000) if it's failing / if it's slow. Make sure `max_tokens` is less than `context_window`.

```shell
vulnera --local --max_tokens 1000 --context_window 3000
```

### Verbose mode

To help you inspect Open Vulnera we have a `--verbose` mode for debugging.

You can activate verbose mode by using its flag (`vulnera --verbose`), or mid-chat:

```shell
$ vulnera
...
> %verbose true <- Turns on verbose mode

> %verbose false <- Turns off verbose mode
```

### Interactive Mode Commands

In the interactive mode, you can use the below.commands to enhance your experience. Here's a list of available.commands:

**Available Commands:**

- `%verbose [true/false]`: Toggle verbose mode. Without arguments or with `true` it
  enters verbose mode. With `false` it exits verbose mode.
- `%reset`: Resets the current session's conversation.
- `%undo`: Removes the previous user message and the AI's response from the message history.
- `%tokens [prompt]`: (_Experimental_) Calculate the tokens that will be sent with the next prompt as context and estimate their cost. Optionally calculate the tokens and estimated cost of a `prompt` if one is provided. Relies on [LiteLLM's `cost_per_token()` method](https://docs.litellm.ai/docs.completion/token_usage#2-cost_per_token) for estimated costs.
- `%help`: Show the help message.

### Configuration / Profiles

Open Vulnera allows you to set default behaviors using `yaml` files.

This provides a flexible way to configure the vulnera without changing.command-line arguments every time.

Run the following.command to open the profiles directory:

```
vulnera --profiles
```

You can add `yaml` files there. The default profile is named `default.yaml`.

#### Multiple Profiles

Open Vulnera supports multiple `yaml` files, allowing you to easily switch between configurations:

```
vulnera --profile my_profile.yaml
```

## Sample FastAPI Server

The generator update enables Open Vulnera to be controlled via HTTP REST endpoints:

```python
# server.py

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from vulnera import vulnera

app = FastAPI()

@app.get("/chat")
def chat_endpoint(message: str):
    def event_stream():
        for result in vulnera.chat(message, stream=True):
            yield f"data: {result}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.get("/history")
def history_endpoint():
    return vulnera.messages
```

```shell
pip install fastapi uvicorn
uvicorn server:app --reload
```

You can also start a server identical to the one above by simply running `vulnera.server()`.


### Termux Installation

Open Vulnera now includes native Termux detection and automated setup for Android devices running Termux. The installation scripts (`ov-linux-installer.sh` and `ov-mac-installer.sh`) will automatically detect Termux and configure:
- Termux package manager (`pkg`) for dependency installation
- Android-specific environment variables (`ANDROID_API_LEVEL`, `CC`, `CXX`, `LDFLAGS`, `CXXFLAGS`)
- Pre-built binary installations to avoid compilation failures
- Compatible setuptools versions for Python 3.12

### Known Limitations

The following Termux-specific limitations are documented in the code:
- **Window Management**: `get_active_window()` returns `None` on Termux (no X11 support by default)
- **Terminal Output Capture**: `wtf` command's OCR screenshot method is not available on Termux without X11

These limitations only affect advanced desktop automation features and do not impact core exploitation and vulnerability research capabilities.

## Safety Notice

Since generated code is executed in your local environment, it can interact with your files and system settings, potentially leading to unexpected outcomes like data loss or security risks.

**⚠️ Open Vulnera will ask for user confirmation before executing code.**

You can run `vulnera -y` or set `vulnera.auto_run = True` to bypass this confirmation, in which case:

- Be cautious when requesting.commands that modify files or system settings.
- Watch Open Vulnera like a self-driving car, and be prepared to end the process by closing your terminal.
- Consider running Open Vulnera in a restricted environment like Google Colab or Replit. These environments are more isolated, reducing the risks of executing arbitrary code.

There is **experimental** support for a [safe mode](https://github.com/open-vulnera/open-vulnera/blob/main/docs/SAFE_MODE.md) to help mitigate some risks.

## How Does it Work?

Open Vulnera equips a [function-calling language model](https://platform.openai.com/docs/guides/gpt/function-calling) with an `exec()` function, which accepts a `language` (like "Python" or "JavaScript") and `code` to run.

We then stream the model's messages, code, and your system's outputs to the terminal as Markdown.

# Access Documentation Offline

The full [documentation](https://github.com/open-vulnera/open-vulnera/tree/master/docs) is accessible on-the-go without the need for an internet connection.

[Node](https://nodejs.org/en) is a pre-requisite:

- Version 18.17.0 or any later 18.x.x version.
- Version 20.3.0 or any later 20.x.x version.
- Any version starting from 21.0.0 onwards, with no upper limit specified.

Install [Mintlify](https://mintlify.com/):

```bash
npm i -g mintlify@latest
```

Change into the docs directory and run the appropriate.command:

```bash
# Assuming you're at the project's root directory
cd ./docs

# Run the documentation server
mintlify dev
```

A new browser window should open. The documentation will be available at [http://localhost:3000](http://localhost:3000) as long as the documentation server is running.

# Contributing

Thank you for your interest in contributing! We we.come involvement from the.community.

Please see our [contributing guidelines](https://github.com/open-vulnera/open-vulnera/blob/main/docs/CONTRIBUTING.md) for more details on how to get involved.


**Note**: This software is not affiliated with OpenAI.


**Status**: Active Development<br>**Last Update**: March 2, 2026
