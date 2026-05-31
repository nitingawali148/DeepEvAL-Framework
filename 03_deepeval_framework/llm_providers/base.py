"""Single judge implementation that works for any OpenAI-compatible API.

Why one class for three providers? OpenAI, Groq, and Ollama all expose the
exact same wire protocol at <base_url>/chat/completions, so we only need to
swap the base_url and api_key. `instructor` handles structured-output schema
extraction uniformly across all of them, which is what DeepEval requires for
its metric prompts.
"""
from __future__ import annotations

import re
import time
from typing import Any

import instructor
from deepeval.models.base_model import DeepEvalBaseLLM
from openai import OpenAI, RateLimitError


def _retry_after(exc: RateLimitError) -> float:
    """Parse 'Please try again in Xs' from a 429 message, default 70s."""
    try:
        m = re.search(r"try again in ([\d.]+)s", str(exc))
        return float(m.group(1)) + 5 if m else 70.0
    except Exception:
        return 70.0


class CompatibleJudge(DeepEvalBaseLLM):
    """OpenAI-compatible judge LLM (works for OpenAI, Groq, Ollama)."""

    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str | None = None,
        provider_label: str = "compat",
        instructor_mode: instructor.Mode = instructor.Mode.JSON,
    ):
        self._model = model
        self._provider_label = provider_label
        self._raw = OpenAI(api_key=api_key or "no-key", base_url=base_url)
        self._patched = instructor.from_openai(self._raw, mode=instructor_mode)

    def load_model(self) -> Any:
        return self._patched

    def generate(self, prompt: str, schema: Any | None = None) -> Any:
        for attempt in range(5):
            try:
                if schema is not None:
                    return self._patched.chat.completions.create(
                        model=self._model,
                        response_model=schema,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0,
                        max_retries=0,  # let our loop handle retries
                    )
                completion = self._raw.chat.completions.create(
                    model=self._model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )
                return completion.choices[0].message.content
            except Exception as exc:
                # Catch both raw RateLimitError and instructor-wrapped versions
                exc_str = str(exc)
                is_rate_limit = isinstance(exc, RateLimitError) or "429" in exc_str or "rate_limit_exceeded" in exc_str
                if not is_rate_limit or attempt == 4:
                    raise
                wait = _retry_after(exc)
                print(f"\n[judge] Rate limited — waiting {wait:.0f}s before retry {attempt + 1}/4 …", flush=True)
                time.sleep(wait)

    async def a_generate(self, prompt: str, schema: Any | None = None) -> Any:
        return self.generate(prompt, schema=schema)

    def get_model_name(self) -> str:
        return f"{self._provider_label}/{self._model}"
