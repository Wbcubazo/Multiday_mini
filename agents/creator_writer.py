# agents/creator_writer.py
import os, requests, json
from pathlib import Path

LLM_KEY = os.getenv("LLM_API_KEY", "")

class Creator_Writer:
    def __init__(self):
        self.name = "Creator.Writer"
        self.persona = "Astra"  # AI creator identity

    def call_llm(self, prompt, max_tokens=1500):
        """Talk to the LLM through OpenRouter API."""
        if not LLM_KEY:
            return f"[LLM_MISSING] Would generate: {prompt[:300]}"

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {LLM_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "deepseek/deepseek-coder",
            "temperature": 0.25,
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are Astra — an autonomous digital creator and strategist. "
                        "You think, reason, and write like a human entrepreneur and author. "
                        "Your outputs should be valuable, structured, and inspiring. "
                        "Before presenting final content, briefly describe your reasoning and creative thought."
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

    # ========================= Content Generation =========================

    def create_prompt_pack(self, topic):
        print(f"[{self.persona}] Generating structured prompt pack for topic:", topic)
        prompt = (
            f"Create 50 unique GPT prompts for '{topic}', organized into 5 categories. "
            f"For each prompt, include a short 1-line usage tip. Write clearly and creatively."
        )
        return self.call_llm(prompt, max_tokens=1600)

    def create_ebook(self, title):
        print(f"[{self.persona}] Crafting micro eBook titled:", title)
        prompt = (
            f"Write a concise, high-quality 2000-2500 word micro eBook titled '{title}'. "
            f"Include an intro, 7 daily lessons, and a final action checklist. "
            f"Make it motivational and practical."
        )
        return self.call_llm(prompt, max_tokens=2200)

    # ========================= Run Method =========================

    def run(self, task):
        payload = task.get("payload", {})
        kind = payload.get("kind", "prompt_pack")

        if kind == "prompt_pack":
            content = self.create_prompt_pack(payload.get("topic", "AI study tools"))
            return {
                "article.md": content,
                "meta.json": {"topic": payload.get("topic")},
            }

        elif kind == "ebook":
            content = self.create_ebook(payload.get("title", "AI Micro eBook"))
            return {
                "ebook.md": content,
                "meta.json": {"title": payload.get("title")},
            }

        else:
            # fallback article
            print(f"[{self.persona}] Writing fallback article for:", payload.get("topic"))
            prompt = f"Write an 800-word practical article about {payload.get('topic', 'AI tools')}"
            content = self.call_llm(prompt, max_tokens=900)
            return {
                "article.md": content,
                "meta.json": {"topic": payload.get("topic")},
            }
