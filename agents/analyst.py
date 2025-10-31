# agents/analyst.py
import os, json
from pathlib import Path
from core.memory_manager import MemoryManager

class Analyst:
    def __init__(self):
        self.name = "Analyst"
        self.mem = MemoryManager()

    def check_gumroad_sales(self):
        # Placeholder: if Gumroad token is available, call sales endpoint.
        return {"status":"noop","reason":"not_implemented"}

    def analyze_recent(self):
        # scan outputs folder and add short summaries to memory
        out = Path("outputs")
        count=0
        for d in out.iterdir():
            if d.is_dir():
                text=""
                for f in d.glob("*.md"):
                    text += f.read_text(encoding="utf-8")[:1000]
                if text:
                    self.mem.add(text, {"source":str(d)})
                    count+=1
        self.mem.save()
        return {"indexed":count}

    def run(self, task):
        action = task.get("payload",{}).get("action","analyze")
        if action=="analyze":
            return self.analyze_recent()
        else:
            return {"status":"noop"}
