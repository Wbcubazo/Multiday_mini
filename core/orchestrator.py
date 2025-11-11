# core/orchestrator.py
import time
import json
import os
import inspect
from core.task_queue import pop_next
from importlib import import_module
from pathlib import Path

# Map logical agent name (task.to) -> python module path
AGENT_MAP = {
    "Commander": "agents.commander",
    "Creator.Writer": "agents.creator_writer",
    "Publisher": "agents.publisher",
    "Marketer": "agents.marketer",
    "Analyst": "agents.analyst"
}

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)  # ensure outputs exists (so artifact upload sees folder)

def _call_module_run_if_available(module, task):
    """
    If module exposes a top-level callable `run(task)` function, call it.
    Return result or None if not present.
    """
    if hasattr(module, "run") and callable(getattr(module, "run")):
        return module.run(task)
    return None

def _find_agent_class_and_invoke(module, task):
    """
    Find a class inside module that has a callable `run` method, instantiate it (no args),
    and call instance.run(task). This supports varied class naming styles.
    """
    for name, obj in inspect.getmembers(module, inspect.isclass):
        # Only consider classes defined in this module
        if getattr(obj, "__module__", None) != module.__name__:
            continue
        if hasattr(obj, "run") and callable(getattr(obj, "run")):
            try:
                instance = obj()
            except Exception as e:
                # If instantiation fails, continue to next candidate
                print(f"[orchestrator] Could not instantiate {name}: {e}")
                continue
            return instance.run(task)
    # no suitable class found
    raise AttributeError(f"No class with callable 'run(task)' found in module {module.__name__}")

def dispatch(task):
    """
    Dispatch a single task dict to the appropriate agent.
    Task must include "to" and "task_id".
    """
    to = task.get("to")
    if not to:
        raise ValueError("Task missing 'to' field")

    module_path = AGENT_MAP.get(to)
    if not module_path:
        raise ValueError(f"No agent registered for target: {to}")

    # Import module
    try:
        module = import_module(module_path)
    except Exception as e:
        raise ImportError(f"Failed to import module {module_path}: {e}")

    # 1) Try module-level run(task)
    try:
        res = _call_module_run_if_available(module, task)
        if res is not None:
            return res
    except Exception as e:
        raise RuntimeError(f"Module-level run() raised an exception in {module_path}: {e}")

    # 2) Search for a class in module that implements run()
    try:
        res = _find_agent_class_and_invoke(module, task)
        return res
    except AttributeError as ae:
        raise AttributeError(
            f"No suitable run() found in module {module_path}. "
            f"Either export a top-level run(task) function, or "
            f"define a class in {module_path} with a 'run(self, task)' method. "
            f"Original error: {ae}"
        )
    except Exception as e:
        raise RuntimeError(f"Error while invoking agent in {module_path}: {e}")

def run_cycle(max_tasks=10):
    """
    Execute up to max_tasks from the queue.
    Returns list of execution summaries.
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
            # save artifacts to outputs/task_id/ if res is a dict
            task_out_dir = OUTPUT_DIR / tid
            task_out_dir.mkdir(parents=True, exist_ok=True)
            if isinstance(res, dict):
                for fname, content in res.items():
                    outpath = task_out_dir / fname
                    if isinstance(content, (dict, list)):
                        outpath.write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")
                    else:
                        outpath.write_text(str(content), encoding="utf-8")
            executed.append({"task_id": tid, "status": "done"})
        except Exception as e:
            print(f"[orchestrator] Task {tid} failed: {e}")
            executed.append({"task_id": tid, "status": "failed", "error": str(e)})
    return executed
