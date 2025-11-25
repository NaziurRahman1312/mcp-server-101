"""
Embedding helper built on top of sentence-transformers.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Iterable, List

import numpy as np
from sentence_transformers import SentenceTransformer

from mcp_server.core.config import get_settings


@lru_cache
def _load_model() -> SentenceTransformer:
    settings = get_settings()
    return SentenceTransformer(settings.embedding_model_name)


def embed_texts(texts: Iterable[str]) -> List[np.ndarray]:
    model = _load_model()
    vectors = model.encode(list(texts), convert_to_numpy=True, normalize_embeddings=True)
    return [np.asarray(vec, dtype="float32") for vec in vectors]


