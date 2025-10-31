# main.py
import os, time
from agents.commander import Commander
from core.orchestrator import run_cycle

SLEEP_SECONDS = int(os.getenv("LOOP_SLEEP_SECONDS", 86400))  # default 24h

def bootstrap():
    # run commander to convert command.txt into tasks
    c = Commander()
    c.run(None)
    # run an orchestrator cycle to process tasks
    results = run_cycle(max_tasks=20)
    print("Cycle results:", results)

if __name__ == "__main__":
    # Run once (for Colab/GitHub Action). For continuous local run use while loop.
    bootstrap()
