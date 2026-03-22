import json
import os
import threading
import time
from vulnera.terminal_interface.utils.ov_dir import ov_dir


class RagManager:
    def __init__(self, session_id=None):
        self.session_id = session_id or f"session_{int(time.time())}"
        self.entries = []
        self._lock = threading.Lock()

        self.storage_path = os.path.join(ov_dir, "rag")
        os.makedirs(self.storage_path, exist_ok=True)
        self.file_path = os.path.join(self.storage_path, f"{self.session_id}.json")

        self.load()

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    self.entries = data
            except Exception:
                self.entries = []

    def save(self):
        with self._lock:
            with open(self.file_path + ".tmp", "w", encoding="utf-8") as f:
                json.dump(self.entries, f, indent=2)
            os.replace(self.file_path + ".tmp", self.file_path)

    def add_entry(self, target, phase, command, output):
        entry = {
            "timestamp": time.time(),
            "target": target,
            "phase": phase,
            "command": command,
            "output": output,
        }
        self.entries.append(entry)
        self.save()

    def retrieve(self, target=None, phase=None, query="", top_k=3):
        candidates = []

        for entry in self.entries:
            score = 0
            if target and entry.get("target") and target.lower() in entry.get("target").lower():
                score += 5
            if phase and entry.get("phase") and phase.lower() in entry.get("phase").lower():
                score += 3

            text = " ".join([str(entry.get("command", "")), str(entry.get("output", ""))]).lower()
            if query:
                if query.lower() in text:
                    score += 4
                for term in query.lower().split():
                    if term in text:
                        score += 1

            # Favor recent entries also
            score += max(0, 2 - ((time.time() - entry.get("timestamp", time.time())) / 3600))

            if score > 0:
                candidates.append((score, entry))

        candidates.sort(key=lambda x: x[0], reverse=True)
        return [c[1] for c in candidates[:top_k]]


rag_manager = None

def get_rag_manager(session_id=None):
    global rag_manager
    if rag_manager is None:
        rag_manager = RagManager(session_id=session_id)
    return rag_manager
