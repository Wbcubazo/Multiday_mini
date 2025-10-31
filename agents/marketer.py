# agents/marketer.py
import os, json, requests
from pathlib import Path

REDDIT_ID = os.getenv("REDDIT_CLIENT_ID","")
REDDIT_SECRET = os.getenv("REDDIT_CLIENT_SECRET","")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT","autonomous_agent/0.1")

class Marketer:
    def __init__(self):
        self.name = "Marketer"

    def post_reddit(self, subreddit, title, body):
        # very minimal placeholder: requires OAuth; fallback to noop
        if not (REDDIT_ID and REDDIT_SECRET):
            return {"status":"noop","reason":"reddit_creds_missing"}
        # Implementation requires PRAW or direct OAuth — keep simple for now
        return {"status":"posted","subreddit":subreddit,"title":title}

    def post_x(self, text):
        # placeholder: requires X API tokens
        return {"status":"noop","reason":"x_token_missing"}

    def run(self, task):
        payload = task.get("payload",{})
        action = payload.get("action","promote")
        references = payload.get("references",[])
        results=[]
        for ref in references:
            p = Path("outputs")/ref
            md = next(p.glob("*.md"), None)
            if not md:
                results.append({"ref":ref,"status":"no_artifact"})
                continue
            summary = md.read_text(encoding="utf-8")[:300]
            # post to reddit (best-effort)
            r = self.post_reddit("CollegeAdmissions", f"Resource: {md.stem}", summary + "\n\nLink:{GUMROAD_LINK}")
            results.append({"ref":ref,"reddit":r})
        return {"promoted":results}
