"""Metric #12: RAG Answer Relevancy."""
import pytest
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase


@pytest.mark.rag
@pytest.mark.quality
@pytest.mark.slow
@pytest.mark.needs_rag
def test_rag_answer_relevancy(rag, rag_alive, rag_goldens, judge):
    assert rag_alive
    metric = AnswerRelevancyMetric(threshold=0.7, model=judge, include_reason=True)
    failures = []
    for g in rag_goldens:
        result = rag.chat(g.input)
        tc = LLMTestCase(input=g.input, actual_output=result.answer)
        metric.measure(tc)
        if not metric.is_successful():
            failures.append((g.input, metric.score, metric.reason))
    assert not failures, f"RAG answer-relevancy failures: {failures}"
