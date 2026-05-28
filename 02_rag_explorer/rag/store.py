"""Vector store with ChromaDB support and an in-memory fallback."""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

try:
    import chromadb
    from chromadb.config import Settings
except Exception:  # pragma: no cover - fallback path for local runs
    chromadb = None
    Settings = None

from .ingest import Chunk

DB_DIR = os.getenv(
    "CHROMA_DIR", str(Path(__file__).resolve().parent.parent / "chroma_db")
)
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "ecommerce_kb")


@dataclass
class Hit:
    id: str
    source: str
    text: str
    score: float
    metadata: dict


class VectorStore:
    def __init__(self, path: str = DB_DIR, collection: str = COLLECTION_NAME):
        self.path = path
        self.collection_name = collection
        self.client = None
        self.collection = None
        self._memory_chunks: list[dict[str, Any]] = []

        if chromadb is not None and Settings is not None:
            try:
                Path(path).mkdir(parents=True, exist_ok=True)
                self.client = chromadb.PersistentClient(
                    path=path,
                    settings=Settings(anonymized_telemetry=False, allow_reset=True),
                )
                self.collection = self.client.get_or_create_collection(
                    name=collection,
                    metadata={"hnsw:space": "cosine"},
                )
                return
            except Exception:
                self.client = None
                self.collection = None

    def _cosine_similarity(
        self, left: Sequence[float], right: Sequence[float]
    ) -> float:
        dot = sum(a * b for a, b in zip(left, right))
        norm_left = math.sqrt(sum(a * a for a in left))
        norm_right = math.sqrt(sum(b * b for b in right))
        if norm_left == 0.0 or norm_right == 0.0:
            return 0.0
        return dot / (norm_left * norm_right)

    def reset(self) -> None:
        if self.client is not None and self.collection is not None:
            try:
                self.client.delete_collection(self.collection.name)
            except Exception:
                pass
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        self._memory_chunks = []

    def add_chunks(
        self, chunks: Sequence[Chunk], embeddings: Sequence[Sequence[float]]
    ) -> int:
        if not chunks:
            return 0

        if self.client is not None and self.collection is not None:
            self.collection.upsert(
                ids=[c.id for c in chunks],
                embeddings=[list(e) for e in embeddings],
                documents=[c.text for c in chunks],
                metadatas=[
                    {
                        "source": c.source,
                        "index": c.index,
                        "char_start": c.char_start,
                        "char_end": c.char_end,
                    }
                    for c in chunks
                ],
            )
            return len(chunks)

        for chunk, embedding in zip(chunks, embeddings):
            self._memory_chunks.append(
                {
                    "id": chunk.id,
                    "source": chunk.source,
                    "text": chunk.text,
                    "metadata": {
                        "source": chunk.source,
                        "index": chunk.index,
                        "char_start": chunk.char_start,
                        "char_end": chunk.char_end,
                    },
                    "embedding": list(embedding),
                }
            )
        return len(chunks)

    def search(self, query_embedding: Sequence[float], top_k: int = 4) -> list[Hit]:
        if self.client is not None and self.collection is not None:
            result = self.collection.query(
                query_embeddings=[list(query_embedding)],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
            hits: list[Hit] = []
            if not result["ids"] or not result["ids"][0]:
                return hits
            for hit_id, doc, meta, dist in zip(
                result["ids"][0],
                result["documents"][0],
                result["metadatas"][0],
                result["distances"][0],
            ):
                hits.append(
                    Hit(
                        id=hit_id,
                        source=meta.get("source", "?"),
                        text=doc,
                        score=max(0.0, 1.0 - float(dist)),
                        metadata=meta,
                    )
                )
            return hits

        scored = []
        for item in self._memory_chunks:
            score = self._cosine_similarity(query_embedding, item["embedding"])
            scored.append((score, item))
        scored.sort(key=lambda entry: entry[0], reverse=True)
        hits = []
        for score, item in scored[:top_k]:
            hits.append(
                Hit(
                    id=item["id"],
                    source=item["source"],
                    text=item["text"],
                    score=score,
                    metadata=item["metadata"],
                )
            )
        return hits

    def stats(self) -> dict[str, Any]:
        if self.client is not None and self.collection is not None:
            count = self.collection.count()
            sources: dict[str, int] = {}
            if count > 0:
                sample = self.collection.get(limit=count, include=["metadatas"])
                for m in sample.get("metadatas") or []:
                    src = m.get("source", "?")
                    sources[src] = sources.get(src, 0) + 1
            return {
                "chunks": count,
                "sources": sources,
                "collection": self.collection.name,
            }

        count = len(self._memory_chunks)
        sources: dict[str, int] = {}
        for item in self._memory_chunks:
            src = item["source"]
            sources[src] = sources.get(src, 0) + 1
        return {"chunks": count, "sources": sources, "collection": "memory"}

    def list_chunks(self, source: str | None = None, limit: int = 200) -> list[dict]:
        if self.client is not None and self.collection is not None:
            result = self.collection.get(
                limit=limit,
                include=["documents", "metadatas"],
                where={"source": source} if source else None,
            )
            items: list[dict] = []
            for cid, doc, meta in zip(
                result["ids"], result["documents"], result["metadatas"]
            ):
                items.append(
                    {
                        "id": cid,
                        "source": meta.get("source", "?"),
                        "index": meta.get("index", 0),
                        "text": doc,
                        "metadata": meta,
                    }
                )
            items.sort(key=lambda x: (x["source"], x["index"]))
            return items

        items = [
            {
                "id": item["id"],
                "source": item["source"],
                "index": item["metadata"].get("index", 0),
                "text": item["text"],
                "metadata": item["metadata"],
            }
            for item in self._memory_chunks
            if source is None or item["source"] == source
        ]
        items.sort(key=lambda x: (x["source"], x["index"]))
        return items[:limit]
