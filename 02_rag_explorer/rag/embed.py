"""Embeddings via Ollama nomic-embed-text (local), with a deterministic fallback."""

from __future__ import annotations

import hashlib
import math
import os
import re
from typing import Sequence

import ollama

EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


def _client() -> ollama.Client:
    return ollama.Client(host=OLLAMA_HOST)


def _fallback_embedding(text: str, dim: int = 64) -> list[float]:
    tokens = re.findall(r"\w+", text.lower())
    if not tokens:
        return [0.0] * dim

    vec = [0.0] * dim
    for i, token in enumerate(tokens):
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        seed = int.from_bytes(digest, "big")
        vec[i % dim] += (seed % 1000) / 1000.0
        vec[(i * 7 + 3) % dim] += ((seed >> 4) % 100) / 100.0

    norm = math.sqrt(sum(v * v for v in vec))
    if norm:
        vec = [v / norm for v in vec]
    return vec


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    if not texts:
        return []

    try:
        client = _client()
        out: list[list[float]] = []
        for t in texts:
            resp = client.embeddings(model=EMBED_MODEL, prompt=t)
            out.append(list(resp["embedding"]))
        return out
    except Exception:
        return [_fallback_embedding(t) for t in texts]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]


def model_info() -> dict:
    return {"model": EMBED_MODEL, "host": OLLAMA_HOST}
