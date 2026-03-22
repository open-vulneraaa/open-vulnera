import json
import os
import threading
import time
from vulnera.terminal_interface.utils.ov_dir import ov_dir


class SessionManager:
    def __init__(self, session_id=None):
        self.session_id = session_id or f"session_{int(time.time())}"
        self.state = {
            "current_target": None,
            "current_objective": None,
            "attack_phase": None,
            "previous_commands": [],
            "previous_outputs": [],
        }
        self._lock = threading.Lock()

        self.session_dir = os.path.join(ov_dir, "sessions")
        os.makedirs(self.session_dir, exist_ok=True)
        self.session_path = os.path.join(self.session_dir, f"{self.session_id}.json")

        self.load_state()

    def load_state(self):
        if os.path.exists(self.session_path):
            try:
                with open(self.session_path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                if isinstance(payload, dict):
                    self.state.update(payload)
            except Exception:
                # ignore corrupt state and reset
                self.state = {
                    "current_target": None,
                    "current_objective": None,
                    "attack_phase": None,
                    "previous_commands": [],
                    "previous_outputs": [],
                }

    def save_state(self):
        with self._lock:
            with open(self.session_path + ".tmp", "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2)
            os.replace(self.session_path + ".tmp", self.session_path)

    def update_from_user(self, text):
        text = (text or "").lower()
        if not text:
            return

        if any(k in text for k in ["target", "hack", "attack", "recon", "scan"]):
            # rudimentary extraction: first host-looking string
            import re

            match = re.search(r"([0-9a-zA-Z.-]+\.[a-z]{2,})", text)
            if match:
                self.state["current_target"] = match.group(1)

        if "deface" in text or "website" in text:
            self.state["current_objective"] = "deface"
        elif "sql" in text or "database" in text or "inject" in text:
            self.state["current_objective"] = "extract_db"
        elif "takeover" in text or "admin" in text:
            self.state["current_objective"] = "admin_takeover"

        if any(k in text for k in ["recon", "scan", "nmap", "enumeration"]):
            self.state["attack_phase"] = "recon"
        elif any(k in text for k in ["exploit", "sqlmap", "sqli", "command injection"]):
            self.state["attack_phase"] = "exploit"
        elif any(k in text for k in ["privilege", "post exploit", "escalate", "root"]):
            self.state["attack_phase"] = "post_exploit"

        self.save_state()

    def add_command(self, command):
        self.state["previous_commands"].append(command)
        self.save_state()

    def add_output(self, output):
        cleaned = output.strip() if isinstance(output, str) else str(output)
        self.state["previous_outputs"].append(cleaned)
        self.save_state()

    def get_state(self):
        return self.state


# helper to expose scoped manager from one call
session_manager = None

def get_session_manager(session_id=None):
    global session_manager
    if session_manager is None:
        session_manager = SessionManager(session_id=session_id)
    return session_manager
