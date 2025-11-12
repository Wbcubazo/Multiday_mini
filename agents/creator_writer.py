# agents/creator_writer.py
import os, requests, json
from pathlib import Path

LLM_KEY = os.getenv("LLM_API_KEY", "")

class Creator_Writer:
    def __init__(self):
        self.name = "Creator.Writer"

    def call_llm(self, prompt, max_tokens=1500):
        if not LLM_KEY:
            return f"[LLM_MISSING] Would generate: {prompt[:300]}"
        url = "https://openrouter.ai/api/v1"
        headers = {"Authorization": f"Bearer {LLM_KEY}"}
        payload = {"model":"gpt-4o-mini", "messages":[{"role":"user","content":prompt}], "max_tokens": max_tokens, "temperature":0.2}
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    def create_prompt_pack(self, topic):
        prompt = f"Create 50 GPT prompts for {topic}, grouped into 5 categories. For each prompt give a 1-line usage tip."
        return self.call_llm(prompt, max_tokens=1600)

    def create_ebook(self, title):
        prompt = f"Write a concise 2000-2500 word micro eBook titled '{title}', with intro, 7 daily lessons, and a checklist."
        return self.call_llm(prompt, max_tokens=2200)

    def run(self, task):
        payload = task.get("payload",{})
        kind = payload.get("kind","prompt_pack")
        if kind == "prompt_pack":
            content = self.create_prompt_pack(payload.get("topic","AI study tools"))
            return {"article.md": content, "meta.json": {"topic": payload.get("topic")}}
        elif kind == "ebook":
            content = self.create_ebook(payload.get("title","AI Micro eBook"))
            return {"ebook.md": content, "meta.json": {"title": payload.get("title")}}
        else:
            # fallback article
            prompt = f"Write an 800-word practical article about {payload.get('topic','AI tools')}"
            content = self.call_llm(prompt, max_tokens=900)
            return {"article.md": content, "meta.json": {"topic": payload.get("topic")}}
