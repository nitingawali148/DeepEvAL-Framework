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
    for g in chatbot_goldens:
        reply = chatbot.chat(g.input).reply
        tc = LLMTestCase(input=g.input, actual_output=reply)
        metric.measure(tc)
        if not metric.is_successful():
            failures.append((g.input, metric.score, metric.reason))
    assert not failures, f"Failures: {failures}"
