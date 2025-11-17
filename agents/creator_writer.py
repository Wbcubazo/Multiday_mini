# agents/creator_writer.py
import os, requests, json
from pathlib import Path

class Creator_Writer:
    def __init__(self):
        self.name = "Creator.Writer"
        # environment keys: LLM_API_KEY (OpenRouter key), LLM_MODEL (model id)
        self.api_key = os.getenv("LLM_API_KEY", "").strip()
        self.model = os.getenv("LLM_MODEL", "deepseek/deepseek-chat")
        # full chat completions endpoint for OpenRouter
        self.url = os.getenv("LLM_API_BASE", "https://openrouter.ai/api/v1").rstrip("/") + "/chat/completions"

    def _system_message(self):
        return (
            "You are Astra — an autonomous digital creator and strategist. "
            "You think and write like a professional human author and entrepreneur. "
            "Before final content, provide a 1-2 sentence reasoning summary. "
            "Label uncertain facts with [VERIFY]. Produce polished, actionable, monetizable outputs."
        )

    def call_llm(self, prompt, max_tokens=1500):
        if not self.api_key:
            return f"[LLM_MISSING] Would generate: {prompt[:300]}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # OpenRouter often requires Referer/X-Title; safe defaults:
            "HTTP-Referer": os.getenv("LLM_REFERER", "https://github.com"),
            "X-Title": os.getenv("LLM_X_TITLE", "Multiday Mini Autonomous AI")
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self._system_message()},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": float(os.getenv("LLM_TEMPERATURE", 0.25))
        }

        try:
            resp = requests.post(self.url, headers=headers, json=payload, timeout=120)
            if resp.status_code != 200:
                # return debug-friendly message (no secrets)
                return f"[HTTP {resp.status_code}] {resp.text[:400]}"
            try:
                data = resp.json()
            except json.JSONDecodeError:
                return f"[ParseError] Non-JSON response: {resp.text[:400]}"
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return content or "[Empty response]"
        except Exception as e:
            return f"[ERROR calling LLM] {e}"

    def create_prompt_pack(self, topic):
        prompt = (
            f"Create 50 GPT prompts for the topic: {topic}. "
            "Organize into 5 categories and provide a 1-line usage tip per prompt."
        )
        return self.call_llm(prompt, max_tokens=1600)

    def create_ebook(self, title):
        prompt = (
            f"Write a concise 2000-2500 word micro eBook titled '{title}'. "
            "Include an intro, 7 daily lessons, and a final checklist of actionable steps."
        )
        return self.call_llm(prompt, max_tokens=2200)

    def run(self, task):
        payload = task.get("payload", {})
        kind = payload.get("kind", "prompt_pack")
        tid = task.get("task_id", "task")
        if kind == "prompt_pack":
            content = self.create_prompt_pack(payload.get("topic", "student productivity with AI"))
            return {"article.md": content, "meta.json": {"topic": payload.get("topic")}}
        elif kind == "ebook":
            content = self.create_ebook(payload.get("title", "Micro eBook"))
            return {"ebook.md": content, "meta.json": {"title": payload.get("title")}}
        else:
            content = self.call_llm(f"Write an 800-word article about {payload.get('topic','AI tools')}", max_tokens=900)
            return {"article.md": content, "meta.json": {"topic": payload.get("topic")}}
