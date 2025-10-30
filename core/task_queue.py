# core/task_queue.py
import json, os
from pathlib import Path
TASKS_FILE = Path("tasks_queue.json")

def load_tasks():
    if not TASKS_FILE.exists():
        return []
    return json.loads(TASKS_FILE.read_text(encoding="utf-8"))

def save_tasks(tasks):
    TASKS_FILE.write_text(json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8")

def push_task(task):
    tasks = load_tasks()
    tasks.append(task)
    save_tasks(tasks)

def pop_next():
    tasks = load_tasks()
    if not tasks:
        return None
    task = tasks.pop(0)
    save_tasks(tasks)
    return task
