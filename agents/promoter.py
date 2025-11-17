# agents/promoter.py
import os, requests, json, time

class Promoter:
    def __init__(self):
        self.name = "Promoter"
        self.identity = "Astra"  # persona continuity

    def announce(self, content, platform="medium"):
        """Simulate posting and trust-building"""
        summary = content[:350]
        msg = (
            f"[{self.identity} - Promoter Agent]\n"
            f"Platform: {platform}\n"
            f"🪩 Post Preview: {summary}\n\n"
            f"Astra explains the 'why' behind the idea to gain trust."
        )
        print(msg)
        self.simulate_trust_growth(platform)

    def simulate_trust_growth(self, platform):
        """Grow credibility metric per post (stored locally)"""
        trust_file = "memory/trust.json"
        data = {"trust_score": 0}
        if os.path.exists(trust_file):
            try:
                data = json.load(open(trust_file))
            except:
                pass
        data["trust_score"] += 1
        json.dump(data, open(trust_file, "w"), indent=2)
        print(f"[{self.identity}] Trust +1 on {platform} (Current trust: {data['trust_score']})")

    def run(self, task):
        payload = task.get("payload", {})
        platform = payload.get("platform", "medium")
        content = payload.get("content", "")
        self.announce(content, platform)
        return {"status": "posted", "trust_metric": True}
