import os, json, random, datetime, requests
from pathlib import Path

LLM_KEY = os.getenv("LLM_API_KEY", "")

class Goal_Planner:
    def __init__(self):
        self.name = "Goal.Planner"
        self.memory_path = Path("memory/context.json")
        self.load_memory()

    def load_memory(self):
        if self.memory_path.exists():
            try:
                with open(self.memory_path, "r") as f:
                    self.memory = json.load(f)
            except:
                self.memory = {"recent_topics": [], "best_performing_titles": []}
        else:
            self.memory = {"recent_topics": [], "best_performing_titles": []}

    def save_memory(self):
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.memory_path, "w") as f:
            json.dump(self.memory, f, indent=2)

    def call_llm(self, prompt):
        if not LLM_KEY:
            return "[LLM_MISSING] No API key found."

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {LLM_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "deepseek/deepseek-coder",
            "temperature": 0.35,
            "max_tokens": 600,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are Atlas — the autonomous planner agent for Astra, "
                        "an AI creator who runs a digital publishing business. "
                        "You analyze memory, decide next tasks, and plan new topics "
                        "that can attract audience or generate revenue."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }

        r = requests.post(url, headers=headers, json=payload, timeout=120)
        r.raise_for_status()

        try:
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[ERROR parsing LLM response] {str(e)}"

    def decide_next_task(self):
        today = datetime.date.today().strftime("%Y-%m-%d")
        topics = [
            "AI business automation",
            "digital solopreneurship",
            "learning with AI",
            "future jobs",
            "AI tools for creators",
            "productivity and focus",
            "AI-driven marketing",
        ]

        last_topics = self.memory.get("recent_topics", [])
        available_topics = [t for t in topics if t not in last_topics]
        topic = random.choice(available_topics or topics)

        self.memory["recent_topics"] = (last_topics + [topic])[-5:]
        self.save_memory()

        print(f"[Atlas] Decided new topic for {today}: {topic}")

        prompt = f"Based on current trends, decide what Astra should create next about '{topic}'. Choose between: [prompt_pack, ebook]. Respond in JSON with keys 'kind', 'title' or 'topic'."
        try:
            raw = self.call_llm(prompt)
            print(f"[Atlas] LLM Response: {raw}")
            data = json.loads(raw)
        except:
            data = {
                "kind": "ebook",
                "title": f"The Power of {topic.title()} in 2025",
            }

        return {
            "task_id": f"t-{today.replace('-', '')}-{random.randint(1000,9999)}",
            "agent": "Creator.Writer",
            "payload": data,
        }
