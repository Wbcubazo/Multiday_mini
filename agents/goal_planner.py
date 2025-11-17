# agents/atlas_goal_planner.py
"""
Atlas Goal Planner (production-level)
Reads command.txt (high-level goal), consults MemoryAgent, and emits TaskSchema tasks.
Produces SMART goals, weekly milestones, and concrete Task JSONs for the Orchestrator.
"""
import os, json, uuid, time
from pathlib import Path
from agents.memory_agent import MemoryAgent
from agents.creator_writer import Creator_Writer

COMMAND_FILE = Path("command.txt")
TASKS_OUT = Path("tasks_queue.json")  # orchestrator uses this file
TASK_SCHEMA_SAMPLE = {
    "task_id": "t-YYYYMMDD-001",
    "from": "Atlas",
    "to": "Creator.Writer",
    "priority": "high",
    "goal": "short descriptor",
    "payload": {},
    "dependencies": [],
    "memory_refs": [],
    "retry_policy": {"max_retries": 2, "backoff_seconds": 60},
    "created_at": ""
}

class AtlasPlanner:
    def __init__(self):
        self.mem = MemoryAgent()
        self.writer = Creator_Writer()
        self.command = self._read_command()
        self.out_path = TASKS_OUT

    def _read_command(self):
        if not COMMAND_FILE.exists():
            return None
        return COMMAND_FILE.read_text(encoding="utf-8").strip()

    def _create_task(self, to, payload, priority="medium", goal="auto-generated", deps=None, mem_refs=None):
        tid = f"t-{uuid.uuid4().hex[:8]}"
        task = {
            "task_id": tid,
            "from": "Atlas",
            "to": to,
            "priority": priority,
            "goal": goal,
            "payload": payload,
            "dependencies": deps or [],
            "memory_refs": mem_refs or [],
            "retry_policy": {"max_retries": 2, "backoff_seconds": 60},
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        return task

    def _plan_from_command(self, cmd_text):
        """
        Use a deterministic, template-based planner. We avoid heavy LLM calls here for predictability,
        but the system can optionally ask LLM for creative planning suggestions.
        """
        # Simple heuristics: if command mentions "week" create weekly milestones, else create 3 tasks
        tasks = []
        # try to extract topics / product types
        # look for quoted strings:
        import re
        quoted = re.findall(r'"([^"]+)"', cmd_text)
        topics = quoted if quoted else []
        # fallback keywords
        if not topics:
            # split by commas and pick top 2-3 tokens
            parts = [p.strip() for p in cmd_text.split(",") if p.strip()]
            if parts:
                topics = parts[:2]
        if not topics:
            topics = ["student productivity with AI"]

        # Create: promptpack + ebook + publish task
        for t in topics[:2]:
            tasks.append(self._create_task(
                to="Creator.Writer",
                payload={"kind":"prompt_pack","topic":t},
                priority="high",
                goal=f"Create prompt pack for {t}"
            ))
            tasks.append(self._create_task(
                to="Creator.Writer",
                payload={"kind":"ebook","title":f"{t} — Micro eBook"},
                priority="medium",
                goal=f"Create ebook for {t}"
            ))

        # Publisher/promotion task (depends on generated artifacts)
        refs = [task["task_id"] for task in tasks if task["to"]=="Creator.Writer"]
        tasks.append(self._create_task(
            to="Publisher",
            payload={"action":"publish_batch", "references": refs},
            priority="high",
            goal="Publish created artifacts",
            deps=refs
        ))
        return tasks

    def _write_tasks(self, tasks):
        # Append to tasks_queue.json (or overwrite if empty)
        existing = []
        if self.out_path.exists():
            try:
                existing = json.loads(self.out_path.read_text(encoding="utf-8"))
            except Exception:
                existing = []
        existing.extend(tasks)
        self.out_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")

    def run(self):
        """
        Main entrypoint: read command, consult memory/top-performers, create tasks, and record plan to memory.
        """
        cmd = self.command or "Autonomous: create one prompt pack and one ebook today for student productivity."
        # optionally consult memory for best topics
        recent = self.mem.summary_recent(10)
        topics = []
        for item in recent:
            meta = item.get("metadata", {})
            if meta.get("topic"):
                topics.append(meta["topic"])
        # choose topics: prefer memory topics if present
        if topics:
            chosen_topic = topics[0]
            cmd = f'Create prompt pack and ebook for \"{chosen_topic}\"'
        tasks = self._plan_from_command(cmd)
        # register plan into memory
        plan_summary = {"plan_cmd": cmd, "tasks": [t["task_id"] for t in tasks], "ts": time.time()}
        self.mem.add_memory(json.dumps(plan_summary), {"type":"plan","source":"Atlas"})
        # write tasks to queue
        self._write_tasks(tasks)
        return {"status":"planned","tasks": [t["task_id"] for t in tasks]}
