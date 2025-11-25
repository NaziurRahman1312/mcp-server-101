"""
Lightweight FAISS store that keeps semantic vectors for resources and tools.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Iterable, List, Literal, Tuple

import faiss
import numpy as np

from mcp_server.core.config import get_settings
from mcp_server.infrastructure.vector.embeddings import embed_texts

VectorTarget = Literal["resource", "tool"]


class FaissStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.index_path = Path(settings.faiss_index_path)
        self.meta_path = self.index_path.with_suffix(".meta.json")
        self.dim = settings.embedding_dim

        self.index = self._load_index()
        self.meta = self._load_meta()

    def _load_index(self) -> faiss.Index:
        if self.index_path.exists():
            return faiss.read_index(str(self.index_path))
        index = faiss.IndexIDMap(faiss.IndexFlatIP(self.dim))
        self._persist_index(index)
        return index

    def _persist_index(self, index: faiss.Index) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(self.index_path))

    def _load_meta(self) -> dict[str, dict[str, str]]:
        if self.meta_path.exists():
            return json.loads(self.meta_path.read_text())
        return {}

    def _persist_meta(self) -> None:
        self.meta_path.parent.mkdir(parents=True, exist_ok=True)
        self.meta_path.write_text(json.dumps(self.meta, indent=2))

    @staticmethod
    def _vector_id(item_type: VectorTarget, entity_id: str) -> int:
        namespace = uuid.uuid5(uuid.NAMESPACE_DNS, f"smart-mcp::{item_type}")
        return uuid.uuid5(namespace, entity_id).int % (2**63 - 1)

    def add_or_update(self, item_type: VectorTarget, entity_id: str, text: str) -> None:
        vector_id = self._vector_id(item_type, entity_id)
        # Remove existing vector if present
        self.index.remove_ids(np.array([vector_id], dtype=np.int64))
        embedding = embed_texts([text])[0]
        embedding = np.asarray([embedding], dtype="float32")
        ids = np.array([vector_id], dtype=np.int64)
        self.index.add_with_ids(embedding, ids)
        self.meta[str(vector_id)] = {"type": item_type, "entity_id": entity_id}
        self._persist_index(self.index)
        self._persist_meta()

    def delete(self, item_type: VectorTarget, entity_id: str) -> None:
        vector_id = self._vector_id(item_type, entity_id)
        self.index.remove_ids(np.array([vector_id], dtype=np.int64))
        self.meta.pop(str(vector_id), None)
        self._persist_index(self.index)
        self._persist_meta()

    def search(self, query: str, limit: int = 5, item_type: VectorTarget | None = None) -> List[Tuple[str, float, VectorTarget]]:
        if self.index.ntotal == 0:
            return []
        query_vec = embed_texts([query])[0].reshape(1, -1)
        scores, ids = self.index.search(query_vec, limit)
        results: List[Tuple[str, float, VectorTarget]] = []
        for score, vector_id in zip(scores[0], ids[0]):
            if vector_id == -1:
                continue
            meta = self.meta.get(str(vector_id))
            if not meta:
                continue
            target_type = meta["type"]
            if item_type and item_type != target_type:
                continue
            results.append((meta["entity_id"], float(score), target_type))  # type: ignore[arg-type]
        return results


