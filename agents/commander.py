# agents/commander.py
import os, time, json, uuid
from core.task_queue import push_task
from pathlib import Path

COMMAND_FILE = "command.txt"

class Commander:
    def __init__(self):
        self.name = "Commander"

    def read_command(self):
        if not Path(COMMAND_FILE).exists():
            return None
        return Path(COMMAND_FILE).read_text(encoding="utf-8").strip()

    def parse_to_tasks(self, text):
        # Very conservative parser: create 3 tasks based on text goal
        base_id = str(uuid.uuid4())[:8]
        tasks = []
        # Task 1: create prompt pack
        tasks.append({
            "task_id": f"t-{base_id}-promptpack",
            "from": "Commander",
            "to": "Creator.Writer",
            "priority": "high",
            "payload": {"kind":"prompt_pack", "topic": self.extract_topic(text)}
        })
        # Task 2: create ebook
        tasks.append({
            "task_id": f"t-{base_id}-ebook",
            "from": "Commander",
            "to": "Creator.Writer",
            "priority": "medium",
            "payload": {"kind":"ebook", "title": self.extract_title(text)}
        })
        # Task 3: marketing + publish (queued after creation)
        tasks.append({
            "task_id": f"t-{base_id}-publish",
            "from": "Commander",
            "to": "Publisher",
            "priority": "high",
            "payload": {"action":"publish_batch", "references":[f"t-{base_id}-promptpack", f"t-{base_id}-ebook"]}
        })
        return tasks

    def extract_topic(self, text):
        # naive topic extraction: look for quoted words or fallback
        import re
        m = re.search(r'"([^"]+)"', text)
        if m:
            return m.group(1)
        # fallback keywords
        if "student" in text.lower():
            return "student productivity with AI"
        return "ai productivity"

    def extract_title(self, text):
        return "Micro eBook — " + (self.extract_topic(text).title())

    def run(self, _task=None):
        cmd = self.read_command()
        if not cmd:
            print("[Commander] No command.txt found or it is empty.")
            return {"status":"no_command"}
        tasks = self.parse_to_tasks(cmd)
        for t in tasks:
            push_task(t)
        print(f"[Commander] Pushed {len(tasks)} tasks.")
        return {"status":"pushed", "tasks":tasks}
