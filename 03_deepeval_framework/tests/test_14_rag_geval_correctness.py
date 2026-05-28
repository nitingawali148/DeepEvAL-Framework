"""Metric #14: G-Eval (Correctness) on RAG output."""
import pytest
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams


@pytest.mark.rag
@pytest.mark.geval
@pytest.mark.slow
@pytest.mark.needs_rag
def test_rag_correctness(rag, rag_alive, rag_goldens, judge):
    assert rag_alive
    metric = GEval(
        name="Correctness",
        criteria=(
            "Score 1.0 if every fact in actual_output is consistent with expected_output. "
            "Penalise wrong numbers, wrong names, or fabricated details. Tolerate phrasing differences."
        ),
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
        model=judge,
        threshold=0.6,
    )
    failures = []
    for g in rag_goldens:
        result = rag.chat(g.input)
        tc = LLMTestCase(
            input=g.input,
            actual_output=result.answer,
            expected_output=g.expected_output,
        )
        metric.measure(tc)
        if not metric.is_successful():
            failures.append((g.input, metric.score, metric.reason))
    assert not failures, f"RAG correctness failures: {failures}"
