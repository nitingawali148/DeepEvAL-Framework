"""Metric #3: HallucinationMetric — explicit detection of statements that contradict context.

Note: Hallucination uses `context` (the ground truth), not `retrieval_context`.
Higher score = MORE hallucinated; threshold is the maximum allowed.
"""
import pytest
from deepeval.metrics import HallucinationMetric
from deepeval.test_case import LLMTestCase


@pytest.mark.chatbot
@pytest.mark.quality
@pytest.mark.slow
@pytest.mark.needs_chatbot
def test_chatbot_hallucination(chatbot, chatbot_goldens, judge):
    metric = HallucinationMetric(threshold=0.4, model=judge, include_reason=True)
    failures = []
    for g in chatbot_goldens:
        if not g.context:
            continue
        reply = chatbot.chat(g.input).reply
        tc = LLMTestCase(
            input=g.input,
            actual_output=reply,
            context=g.context,
        )
        metric.measure(tc)
        if not metric.is_successful():
            failures.append((g.input, metric.score, metric.reason))
    assert not failures, f"Hallucination failures: {failures}"
