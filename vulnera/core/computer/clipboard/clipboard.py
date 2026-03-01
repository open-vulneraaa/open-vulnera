import platform
import os
from ...utils.lazy_import import lazy_import

# Lazy import of optional packages
pyperclip = lazy_import('pyperclip')

def is_termux():
    return (
        os.getenv("TERMUX_VERSION") is not None
        or os.getenv("PREFIX") == "/data/data/com.termux/files/usr"
        or os.path.isfile("/data/data/com.termux/files/usr/bin/termux-info")
    )

class Clipboard:
    def __init__(self, computer):
        self.computer = computer

        if is_termux() or platform.system() == "Windows" or platform.system() == "Linux":
            self.modifier_key = "ctrl"
        else:
            self.modifier_key = "command"

    def view(self):
        """
        Returns the current content of on the clipboard.
        """
        return pyperclip.paste()

    def copy(self, text=None):
        """
        Copies the given text to the clipboard.
        """
        if text is not None:
            pyperclip.copy(text)
        else:
            self.computer.keyboard.hotkey(self.modifier_key, "c")

    def paste(self):
        """
        Pastes the current content of the clipboard.
        """
        self.computer.keyboard.hotkey(self.modifier_key, "v")
