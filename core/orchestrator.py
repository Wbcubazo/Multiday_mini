# orchestrator.py
import time
import traceback

from agents.goal_planner import Goal_Planner
from agents.creator_writer import Creator_Writer
from agents.publisher import Publisher


class Orchestrator:
    def __init__(self):
        print("[System] Initializing agents...")

        self.planner = Goal_Planner()
        self.writer = Creator_Writer()
        self.publisher = Publisher()

        print("[System] Agents loaded: Goal_Planner, Creator_Writer, Publisher")

    def safe_execute(self, func, description):
        """Runs agent method safely with error handling."""
        try:
            print(f"[System] Running: {description}...")
            return func()
        except Exception as e:
            print(f"[ERROR] during {description}: {str(e)}")
            traceback.print_exc()
            return None

    def run_cycle(self):
        print("\n==============================")
        print("🌐  AUTONOMOUS CONTENT CYCLE  ")
        print("==============================\n")

        # Step 1: Planner Decides Next Task
        task = self.safe_execute(
            self.planner.decide_next_task,
            "Goal Planner deciding next task"
        )

        if not task:
            print("[System] ❌ Planner failed. Skipping cycle.")
            return

        print(f"[System] 📝 Next task decided:\n{task}\n")

        # Step 2: Writer Creates Content
        content = self.safe_execute(
            lambda: self.writer.run(task),
            "Creator Writer generating content"
        )

        if not content:
            print("[System] ❌ Writer failed. Skipping cycle.")
            return

        print("[System] ✍️ Content generated successfully.")

        # Step 3: Publisher Publishes Output
        publish_status = self.safe_execute(
            lambda: self.publisher.publish(content),
            "Publisher saving output"
        )

        if publish_status is None:
            print("[System] ❌ Publisher failed.")
        else:
            print("[System] 📤 Content published successfully.")

        print("\n==============================")
        print("✅  CYCLE COMPLETED SUCCESSFULLY")
        print("==============================\n")
