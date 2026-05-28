"""Smoke tests — verifies the judge LLM and both target services are reachable."""
import pytest


def test_judge_responds(judge):
    out = judge.generate("Reply with exactly the word: pong")
    assert isinstance(out, str) and len(out) > 0


@pytest.mark.needs_chatbot
def test_chatbot_health(chatbot):
    h = chatbot.health()
    assert h["status"] == "ok"


@pytest.mark.needs_rag
def test_rag_health(rag):
    h = rag.health()
    assert h["status"] == "ok"


@pytest.mark.needs_rag
def test_rag_has_chunks(rag, rag_alive):
    assert rag_alive
    stats = rag.health()["stats"]
    assert stats["chunks"] > 0, "RAG store is empty after seed"
