import json, os

class ValueAgent:
    def __init__(self):
        self.name = "ValueAgent"

    def design_offer(self, ebook_title):
        print(f"[ValueAgent] Designing product for: {ebook_title}")
        return {
            "offer_name": f"Mastering {ebook_title}",
            "price": "9.99 USD",
            "description": f"A digital mini-course + eBook by Astra on {ebook_title}."
        }

    def run(self, task):
        payload = task.get("payload", {})
        ebook_title = payload.get("ebook_title", "AI Creativity")
        offer = self.design_offer(ebook_title)
        json.dump(offer, open("outputs/latest_offer.json", "w"), indent=2)
        print("[ValueAgent] Offer created successfully.")
        return offer
