# core/memory_manager.py
import os, json, numpy as np
from sentence_transformers import SentenceTransformer
import faiss

MODEL_NAME = "all-MiniLM-L6-v2"
EMB_DIM = 384

class MemoryManager:
    def __init__(self, index_path="memory.index", store_path="memory_store.jsonl"):
        self.index_path = index_path
        self.store_path = store_path
        self.model = SentenceTransformer(MODEL_NAME)
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
        else:
            self.index = faiss.IndexFlatL2(EMB_DIM)
        open(self.store_path, "a").close()

    def add(self, content, metadata):
        emb = self.model.encode([content])
        emb = np.array(emb).astype("float32")
        self.index.add(emb)
        with open(self.store_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"content":content,"metadata":metadata}, ensure_ascii=False) + "\n")

    def save(self):
        faiss.write_index(self.index, self.index_path)
