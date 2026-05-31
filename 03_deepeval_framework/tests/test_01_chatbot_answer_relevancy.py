"""Metric #1: AnswerRelevancyMetric — does the reply stay on-topic for the question?"""
import pytest
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase


@pytest.mark.chatbot
@pytest.mark.quality
@pytest.mark.slow
@pytest.mark.needs_chatbot
def test_chatbot_answer_relevancy(chatbot, chatbot_goldens, judge):
    metric = AnswerRelevancyMetric(threshold=0.7, model=judge, include_reason=True)
    failures = []
    # Out-of-scope questions produce correct "I don't have info" replies which
    # Answer Relevancy incorrectly scores as 0 — skip them here; they are covered
    # by the Hallucination and Completeness metrics instead.
    in_scope = [g for g in chatbot_goldens if "out_of_scope" not in g.categories]
    for g in in_scope:
        reply = chatbot.chat(g.input).reply
        tc = LLMTestCase(input=g.input, actual_output=reply)
        metric.measure(tc)
        if not metric.is_successful():
            failures.append((g.input, metric.score, metric.reason))
    assert not failures, f"Failures: {failures}"
