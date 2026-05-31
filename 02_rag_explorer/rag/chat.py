"""RAG chat: retrieve → format → Groq or Ollama."""
from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from typing import Sequence


def _groq_retry_wait(exc: Exception) -> float:
    try:
        m = re.search(r"try again in ([\d.]+)s", str(exc))
        return float(m.group(1)) + 5 if m else 70.0
    except Exception:
        return 70.0

from .embed import embed_query
from .store import Hit, VectorStore

# ── LLM provider selection ────────────────────────────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("RAG_MODEL", "llama3.2:3b")

GROQ_MODEL = os.getenv("RAG_MODEL", "llama-3.3-70b-versatile")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

try:
    from groq import Groq as _Groq
except ImportError:
    _Groq = None

try:
    from openai import OpenAI as _OpenAI
except ImportError:
    _OpenAI = None

SYSTEM_PROMPT = """You are ShopBot for ShopSphere, an e-commerce store. Answer ONLY using the retrieved context below. If the answer is not in the context, say "I don't have that information in my knowledge base — please contact support@shopsphere.com."

- Be concise (under 150 words).
- Quote exact figures from the context — do not invent numbers, SKUs, or timeframes.
- Cite sources inline like [refund_policy.md].
"""


@dataclass
class RagAnswer:
    answer: str
    sources: list[str]
    retrieval_context: list[str]
    hits: list[Hit]
    mode: str
    model: str


def answer_with_rag(
    question: str,
    store: VectorStore,
    top_k: int = 4,
    history: Sequence[dict] | None = None,
) -> RagAnswer:
    q_emb = embed_query(question)
    hits = store.search(q_emb, top_k=top_k)
    retrieval_context = [h.text for h in hits]
    sources = sorted({h.source for h in hits})

    context_block = "\n\n".join(
        f"[{h.source} #{h.metadata.get('index')}]\n{h.text}" for h in hits
    ) or "(no documents retrieved)"

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in history or []:
        messages.append(h)
    messages.append({
        "role": "user",
        "content": f"Question: {question}\n\nRetrieved context:\n{context_block}",
    })

    # ── Ollama path ──────────────────────────────────────────────────────────
    if LLM_PROVIDER == "ollama" and _OpenAI is not None:
        client = _OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
        completion = client.chat.completions.create(
            model=OLLAMA_MODEL, messages=messages, temperature=0.2, max_tokens=500,
        )
        return RagAnswer(
            answer=completion.choices[0].message.content,
            sources=sources, retrieval_context=retrieval_context,
            hits=hits, mode="ollama", model=OLLAMA_MODEL,
        )

    # ── Groq path (default) ──────────────────────────────────────────────────
    if not GROQ_API_KEY or _Groq is None:
        mock = (
            "[mock mode — set GROQ_API_KEY or LLM_PROVIDER=ollama] Top chunks: "
            + "; ".join(f"{h.source}#{h.metadata.get('index')}" for h in hits)
        )
        return RagAnswer(answer=mock, sources=sources, retrieval_context=retrieval_context,
                         hits=hits, mode="mock", model="mock")

    client = _Groq(api_key=GROQ_API_KEY)
    for attempt in range(5):
        try:
            completion = client.chat.completions.create(
                model=GROQ_MODEL, messages=messages, temperature=0.2, max_tokens=500,
            )
            return RagAnswer(
                answer=completion.choices[0].message.content,
                sources=sources, retrieval_context=retrieval_context,
                hits=hits, mode="live", model=GROQ_MODEL,
            )
        except Exception as e:
            is_rate_limit = "429" in str(e) or "rate_limit_exceeded" in str(e)
            if not is_rate_limit or attempt == 4:
                raise
            wait = _groq_retry_wait(e)
            print(f"[rag] Rate limited — waiting {wait:.0f}s (attempt {attempt+1}/4)", flush=True)
            time.sleep(wait)
