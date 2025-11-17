# core/orchestrator.py
import json
import inspect
from importlib import import_module
from pathlib import Path
from core.task_queue import pop_next

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# map task "to" to module path (edit if you renamed modules)
AGENT_MAP = {
    "Commander": "agents.commander",
    "Creator.Writer": "agents.creator_writer",
    "Publisher": "agents.publisher",
    "Marketer": "agents.marketer",
    "Analyst": "agents.analyst",
    "Promoter": "agents.promoter",
    "MemoryAgent": "agents.memory_agent",
    "ValueAgent": "agents.value_agent",
    "Atlas": "agents.atlas_goal_planner"
}

def _call_module_level_run(module, task):
    if hasattr(module, "run") and callable(module.run):
        return module.run(task)
    return None

def _find_class_and_run(module, task):
    for _, cls in inspect.getmembers(module, inspect.isclass):
        if getattr(cls, "__module__", None) != module.__name__:
            continue
        if hasattr(cls, "run") and callable(getattr(cls, "run")):
            try:
                inst = cls()
            except Exception as e:
                print(f"[orchestrator] Could not instantiate {cls}: {e}")
                continue
            return inst.run(task)
    raise AttributeError(f"No runnable class/run callable found in {module.__name__}")

def dispatch(task):
    to = task.get("to")
    if not to:
        raise ValueError("Task missing 'to' field")
    module_path = AGENT_MAP.get(to)
    if not module_path:
        raise ValueError(f"No agent registered for target: {to}")
    module = import_module(module_path)
    # 1) module-level run
    try:
        res = _call_module_level_run(module, task)
        if res is not None:
            return res
    except Exception as e:
        raise RuntimeError(f"Module-level run error in {module_path}: {e}")
    # 2) class-level run
    return _find_class_and_run(module, task)

def run_cycle(max_tasks=20):
    """
    Run up to max_tasks sequentially, keeping artifacts in outputs/<task_id> and
    returning a list of execution summaries.
    """
    executed = []
    for _ in range(max_tasks):
        task = pop_next()
        if not task:
            break
        tid = task.get("task_id", "task")
        try:
            print(f"[orchestrator] Dispatching {tid} -> {task.get('to')}")
            res = dispatch(task)
            # normalize result into dict artifacts
            task_out_dir = OUTPUT_DIR / tid
            task_out_dir.mkdir(parents=True, exist_ok=True)
            returned = {}
            if isinstance(res, dict):
                for fname, content in res.items():
                    p = task_out_dir / fname
                    if isinstance(content, (dict, list)):
                        p.write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")
                    else:
                        p.write_text(str(content), encoding="utf-8")
                    returned[fname] = content
            else:
                # if agent returned plain text, save as output.txt
                p = task_out_dir / "output.txt"
                p.write_text(str(res), encoding="utf-8")
                returned["output.txt"] = str(res)
            executed.append({"task_id": tid, "status": "done", "artifacts": list(returned.keys())})
        except Exception as e:
            print(f"[orchestrator] Task {tid} failed: {e}")
            executed.append({"task_id": tid, "status": "failed", "error": str(e)})
    return executed
