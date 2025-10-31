# agents/publisher.py
import os, json, requests
from pathlib import Path

GUMROAD_TOKEN = os.getenv("GUMROAD_ACCESS_TOKEN","")

class Publisher:
    def __init__(self):
        self.name = "Publisher"

    def upload_to_gumroad(self, title, description, price_cents, file_path, preview_image_path=None):
        if not GUMROAD_TOKEN:
            return {"status":"noop","reason":"gumroad_token_missing", "title":title}
        url = "https://api.gumroad.com/v2/products"
        files = {"file": open(file_path,"rb")}
        data = {"product[name]": title, "product[description]": description, "pricing": json.dumps({"default_price": price_cents})}
        headers = {"Authorization": f"Bearer {GUMROAD_TOKEN}"}
        # Gumroad's official API may vary; this is a conservative approach; you may need to create products via web UI and use API for sales.
        r = requests.post(url, headers=headers, data=data, files=files, timeout=60)
        return r.json()

    def run(self, task):
        payload = task.get("payload",{})
        action = payload.get("action")
        if action == "publish_batch":
            refs = payload.get("references",[])
            results = []
            for ref in refs:
                # read outputs/ref/
                p = Path("outputs")/ref
                if not p.exists():
                    results.append({"ref":ref,"status":"missing"})
                    continue
                # pick first markdown or pdf
                md = next(p.glob("*.md"), None)
                if not md:
                    results.append({"ref":ref,"status":"no_artifact"})
                    continue
                title = md.stem
                desc = md.read_text(encoding="utf-8")[:500]
                # package file
                zip_path = str(p) + ".zip"
                import zipfile
                with zipfile.ZipFile(zip_path, "w") as z:
                    for f in p.iterdir():
                        z.write(f, arcname=f.name)
                # upload
                res = self.upload_to_gumroad(title, desc, 900, zip_path)
                results.append({"ref":ref,"upload":res})
            return {"published":results}
        else:
            return {"status":"noop","reason":"unknown_action"}
