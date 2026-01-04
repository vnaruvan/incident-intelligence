# app/llm/embeddings.py

import os
import hashlib
import random
from typing import List, Tuple, Optional

from app.core.config import OPENAI_API_KEY, VECTOR_DIM

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


class EmbeddingError(Exception):
    pass


def _local_deterministic_embedding(text: str, dim: int) -> List[float]:
    # Stable seed from text so results are repeatable across runs/machines
    h = hashlib.sha256(text.encode("utf-8")).digest()
    seed = int.from_bytes(h[:8], "big", signed=False)
    rng = random.Random(seed)

    # Simple deterministic vector in [-1, 1]
    vec = [(rng.random() * 2.0 - 1.0) for _ in range(dim)]

    norm = sum(x * x for x in vec) ** 0.5
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def generate_vector_embeddings(text: str, model: str = "text-embedding-3-small") -> Tuple[List[float], str]:
    """
    Returns (embedding_vector, model_name) or raises EmbeddingError.
    """
    if not text or not text.strip():
        raise EmbeddingError("Text is empty or whitespace only.")

    # Force local mode if no key or explicitly requested
    mode = os.getenv("EMBEDDINGS_MODE", "").lower()  # set to "local" to force
    if mode == "local" or not OPENAI_API_KEY or OpenAI is None:
        vec = _local_deterministic_embedding(text, VECTOR_DIM)
        return vec, "local-deterministic-v1"

    # OpenAI mode (costs money). Only used if key exists and EMBEDDINGS_MODE != local.
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        resp = client.embeddings.create(model=model, input=text)
        vec = resp.data[0].embedding
        if len(vec) != VECTOR_DIM:
            raise EmbeddingError(f"Unexpected embedding dim {len(vec)} != {VECTOR_DIM}")
        return vec, model
    except Exception as e:
        raise EmbeddingError(str(e)) from e
