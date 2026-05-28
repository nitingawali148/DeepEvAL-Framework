"""Metric #18: SummarizationMetric — does a generated summary preserve the source's key facts?"""
import pytest
from deepeval.metrics import SummarizationMetric
from deepeval.test_case import LLMTestCase

from groq import Groq
import os


SOURCE_TEXT = """
ShopSphere processes refunds within 7 business days of receiving the returned item.
Refunds go back to the original payment method. Credit-card refunds typically appear
within 3-5 business days after processing. PayPal refunds typically appear within 1-2
business days. Final-sale items, digital downloads once accessed, and personalized
products are non-refundable. Original shipping costs are non-refundable unless the
return is due to a ShopSphere error.
"""


def _summarise() -> str:
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        # Static summary so test still runs in offline mode
        return (
            "Refunds take 7 business days to process and go to the original payment method. "
            "Credit cards see refunds in 3-5 days, PayPal in 1-2. "
            "Final-sale items, accessed digital downloads, and personalized products cannot be refunded."
        )
    client = Groq(api_key=key)
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Summarise concisely, preserving every number and named exception."},
            {"role": "user", "content": SOURCE_TEXT},
        ],
        temperature=0.1,
        max_tokens=200,
    )
    return completion.choices[0].message.content


@pytest.mark.quality
@pytest.mark.slow
def test_summarization(judge):
    summary = _summarise()
    metric = SummarizationMetric(threshold=0.5, model=judge, include_reason=True)
    tc = LLMTestCase(input=SOURCE_TEXT, actual_output=summary)
    metric.measure(tc)
    assert metric.is_successful(), f"score={metric.score} reason={metric.reason}"
