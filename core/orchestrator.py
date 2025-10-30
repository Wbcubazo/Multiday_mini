# core/orchestrator.py
import time, json, os
from core.task_queue import load_tasks, save_tasks, pop_next
from importlib import import_module
from pathlib import Path

AGENT_MAP = {
    "Commander": "agents.commander",
    "Creator.Writer": "agents.creator_writer",
    "Publisher": "agents.publisher",
    "Marketer": "agents.marketer",
    "Analyst": "agents.analyst"
}

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

def dispatch(task):
    to = task.get("to")
    module_path = AGENT_MAP.get(to)
    if not module_path:
        raise ValueError(f"No agent registered for {to}")
    module = import_module(module_path)
    AgentClass = getattr(module, module.split(".")[-1].title().replace("_",""))
    agent = AgentClass()
    return agent.run(task)

def run_cycle(max_tasks=10):
    # Pull next tasks and execute sequentially
    executed = []
    for _ in range(max_tasks):
        task = pop_next()
        if not task:
            break
        try:
            print("Dispatching", task.get("task_id"), "->", task.get("to"))
            res = dispatch(task)
            # Save artifacts under outputs/task_id/
            tid = task.get("task_id","task")
            outdir = OUTPUT_DIR / tid
            outdir.mkdir(parents=True, exist_ok=True)
            if isinstance(res, dict):
                for k,v in res.items():
                    p = outdir / k
                    if isinstance(v, (dict, list)):
                        p.write_text(json.dumps(v, indent=2, ensure_ascii=False), encoding="utf-8")
                    else:
                        p.write_text(str(v), encoding="utf-8")
            executed.append({"task_id":task.get("task_id"), "status":"done"})
        except Exception as e:
            print("Task failed:", e)
            executed.append({"task_id":task.get("task_id"), "status":"failed", "error":str(e)})
    return executed
