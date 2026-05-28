"""Metric #2: FaithfulnessMetric — every claim in the reply is backed by the retrieval context."""
import pytest
from deepeval.metrics import FaithfulnessMetric
from deepeval.test_case import LLMTestCase


@pytest.mark.chatbot
@pytest.mark.quality
@pytest.mark.slow
@pytest.mark.needs_chatbot
def test_chatbot_faithfulness(chatbot, chatbot_goldens, judge):
    metric = FaithfulnessMetric(threshold=0.7, model=judge, include_reason=True)
    failures = []
    for g in chatbot_goldens:
        if not g.context:
            continue  # faithfulness needs ground-truth context
        reply = chatbot.chat(g.input).reply
        tc = LLMTestCase(
            input=g.input,
            actual_output=reply,
            retrieval_context=g.context,
        )
        metric.measure(tc)
        if not metric.is_successful():
            failures.append((g.input, metric.score, metric.reason))
    assert not failures, f"Faithfulness failures: {failures}"
