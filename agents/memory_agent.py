# agents/memory_agent.py
"""
MemoryAgent: lightweight FAISS-backed memory + JSON logs.
Stores: publications, task results, trust metrics, experiment outcomes.
Provides: add_memory(content, metadata), query_similar(query, k=5), summary_recent(n=10)
"""
import os, json, time
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss

BASE = Path("memory")
BASE.mkdir(parents=True, exist_ok=True)
STORE = BASE / "memory_store.jsonl"
INDEX = BASE / "memory.index"
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
_EMB_DIM = 384  # matches all-MiniLM-L6-v2

class MemoryAgent:
    def __init__(self):
        self.store_path = str(STORE)
        self.index_path = str(INDEX)
        self.model = SentenceTransformer(MODEL_NAME)
        # load or create FAISS index
        if Path(self.index_path).exists():
            try:
                self.index = faiss.read_index(self.index_path)
            except Exception:
                self.index = faiss.IndexFlatL2(_EMB_DIM)
        else:
            self.index = faiss.IndexFlatL2(_EMB_DIM)
        # ensure store exists
        open(self.store_path, "a").close()

    def _write_store(self, item):
        with open(self.store_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    def add_memory(self, content, metadata):
        """
        Add a memory item: content (string) and metadata (dict).
        Returns mem_id.
        """
        mem_id = f"mem-{int(time.time()*1000)}"
        emb = self.model.encode([content]).astype("float32")
        self.index.add(emb)
        item = {"id": mem_id, "content": content, "metadata": metadata, "ts": time.time()}
        self._write_store(item)
        # persist index
        faiss.write_index(self.index, self.index_path)
        return mem_id

    def query_similar(self, query, k=5):
        """
        Return up to k similar memory items (content + metadata).
        """
        emb = self.model.encode([query]).astype("float32")
        if self.index.ntotal == 0:
            return []
        D, I = self.index.search(emb, k)
        results = []
        # read store lines to list
        with open(self.store_path, "r", encoding="utf-8") as f:
            lines = f.read().strip().splitlines()
        for idx in I[0]:
            if idx < len(lines):
                try:
                    obj = json.loads(lines[idx])
                    results.append(obj)
                except Exception:
                    continue
        return results

    def summary_recent(self, n=10):
        """Return last n memory items (most recent)."""
        with open(self.store_path, "r", encoding="utf-8") as f:
            lines = f.read().strip().splitlines()
        if not lines:
            return []
        last = lines[-n:]
        return [json.loads(l) for l in last]

# quick CLI test helpers (import & call MemoryAgent().add_memory(...))
