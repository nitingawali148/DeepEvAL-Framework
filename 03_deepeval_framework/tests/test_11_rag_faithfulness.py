"""Metric #11: RAG Faithfulness — every claim grounded in retrieval_context."""
import pytest
from deepeval.metrics import FaithfulnessMetric
from deepeval.test_case import LLMTestCase


@pytest.mark.rag
@pytest.mark.quality
@pytest.mark.slow
@pytest.mark.needs_rag
def test_rag_faithfulness(rag, rag_alive, rag_goldens, judge):
    assert rag_alive
    metric = FaithfulnessMetric(threshold=0.7, model=judge, include_reason=True)
    failures = []
    for g in rag_goldens:
        result = rag.chat(g.input)
        tc = LLMTestCase(
            input=g.input,
            actual_output=result.answer,
            retrieval_context=result.retrieval_context,
        )
        metric.measure(tc)
        if not metric.is_successful():
            failures.append((g.input, metric.score, metric.reason))
    assert not failures, f"RAG faithfulness failures: {failures}"
