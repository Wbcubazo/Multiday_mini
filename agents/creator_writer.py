# agents/creator_writer.py
import os, requests, json
from pathlib import Path

class Creator_Writer:
    def __init__(self):
        self.name = "Creator.Writer"
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.model = os.getenv("LLM_MODEL", "deepseek/deepseek-chat")
        self.url = "https://openrouter.ai/api/v1/chat/completions"

    def call_llm(self, prompt, max_tokens=1500):
        """Send the prompt to OpenRouter (DeepSeek model) and return text content."""
        if not self.api_key:
            return f"[LLM_MISSING] Would generate: {prompt[:300]}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # ✅ Required for OpenRouter authentication
            "HTTP-Referer": "https://github.com/Wbcubazo/Multiday_mini",
            "X-Title": "Multiday Mini Autonomous AI System"
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.6
        }

        try:
            resp = requests.post(self.url, headers=headers, json=payload, timeout=60)
            if resp.status_code != 200:
                return f"[HTTP {resp.status_code}] {resp.text[:400]}"

            try:
                data = resp.json()
            except json.JSONDecodeError:
                return f"[ParseError] Non-JSON response: {resp.text[:400]}"

            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
            return content or "[Empty response from model]"
        except Exception as e:
            return f"[ERROR calling LLM] {e}"

    def create_prompt_pack(self, topic):
        prompt = (
            f"Create 50 GPT prompts for {topic}, grouped into 5 categories. "
            f"For each prompt, include a 1-line usage tip."
        )
        return self.call_llm(prompt, max_tokens=1600)

    def create_ebook(self, title):
        prompt = (
            f"Write a concise 2000–2500 word micro eBook titled '{title}', "
            f"with an intro, 7 daily lessons, and a final checklist."
        )
        return self.call_llm(prompt, max_tokens=2200)

    def run(self, task):
        payload = task.get("payload", {})
        kind = payload.get("kind", "prompt_pack")

        if kind == "prompt_pack":
            content = self.create_prompt_pack(payload.get("topic", "AI study tools"))
            return {"article.md": content, "meta.json": {"topic": payload.get("topic")}}

        elif kind == "ebook":
            content = self.create_ebook(payload.get("title", "AI Micro eBook"))
            return {"ebook.md": content, "meta.json": {"title": payload.get("title")}}

        else:
            topic = payload.get("topic", "AI tools")
            prompt = f"Write an 800-word practical article about {topic}"
            content = self.call_llm(prompt, max_tokens=900)
            return {"article.md": content, "meta.json": {"topic": topic}}
