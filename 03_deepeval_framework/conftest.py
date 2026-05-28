"""Shared pytest fixtures for the DeepEval framework."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Allow `from llm_providers ...` and `from targets ...` from anywhere
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Load .env if present
load_dotenv(ROOT / ".env")

from llm_providers import get_judge, judge_info  # noqa: E402
from targets import ChatbotClient, RagClient  # noqa: E402


@pytest.fixture(scope="session")
def judge():
    return get_judge()


@pytest.fixture(scope="session", autouse=True)
def _print_judge_banner():
    info = judge_info()
    print(f"\n[deepeval] judge provider={info['provider']!r} model={info['model']!r}")
    yield


@pytest.fixture(scope="session")
def chatbot() -> ChatbotClient:
    return ChatbotClient()


@pytest.fixture(scope="session")
def rag() -> RagClient:
    return RagClient()


@pytest.fixture(scope="session")
def chatbot_alive(chatbot: ChatbotClient) -> bool:
    return chatbot.is_alive()


@pytest.fixture(scope="session")
def rag_alive(rag: RagClient) -> bool:
    alive = rag.is_alive()
    if alive:
        try:
            stats = rag.health().get("stats", {})
            if stats.get("chunks", 0) == 0:
                rag.seed(reset=True)
        except Exception as e:
            print(f"[rag] seed failed: {e}")
    return alive


def pytest_configure(config):
    config.addinivalue_line("markers", "needs_chatbot: skip if chatbot service is down")
    config.addinivalue_line("markers", "needs_rag: skip if RAG service is down")


def pytest_collection_modifyitems(config, items):
    """Auto-skip tests if their target service is offline."""
    chat_ok = ChatbotClient().is_alive()
    rag_ok = RagClient().is_alive()
    skip_chat = pytest.mark.skip(reason="chatbot service not reachable on $CHATBOT_URL")
    skip_rag = pytest.mark.skip(reason="RAG service not reachable on $RAG_URL")
    for item in items:
        if item.get_closest_marker("needs_chatbot") and not chat_ok:
            item.add_marker(skip_chat)
        if item.get_closest_marker("needs_rag") and not rag_ok:
            item.add_marker(skip_rag)


def _max_goldens(cases):
    cap = os.getenv("MAX_GOLDENS")
    if cap and cap.isdigit():
        return cases[: int(cap)]
    return cases


@pytest.fixture(scope="session")
def chatbot_goldens():
    from datasets.chatbot_goldens import CHATBOT_GOLDENS
    return _max_goldens(CHATBOT_GOLDENS)


@pytest.fixture(scope="session")
def rag_goldens():
    from datasets.rag_goldens import RAG_GOLDENS
    return _max_goldens(RAG_GOLDENS)
