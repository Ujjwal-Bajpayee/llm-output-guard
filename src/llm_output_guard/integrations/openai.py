"""OpenAI integration for llm-output-guard."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..core.exceptions import IntegrationError
from ..core.types import SchemaDefinition
from ..core.validator import GuardResult, Validator

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def _check_openai() -> None:
    if not OPENAI_AVAILABLE:
        raise IntegrationError(
            "OpenAI SDK is not installed. Run: pip install openai",
            integration="openai",
        )


class GuardedOpenAI:
    """
    Convenience wrapper that creates a :class:`~llm_output_guard.Validator`
    pre-wired to the OpenAI Chat Completions API.

    Usage::

        from llm_output_guard.integrations.openai import GuardedOpenAI

        guard = GuardedOpenAI(
            schema=MyPydanticModel,
            model="gpt-4o-mini",
            api_key="sk-...",
        )
        result = guard.guard("Summarise the following article: ...")
        print(result.data)
    """

    def __init__(
        self,
        schema: SchemaDefinition,
        *,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        max_retries: int = 2,
        retry_strategy: str = "exponential",
        raise_on_failure: bool = False,
        system_prompt: Optional[str] = None,
        extra_openai_kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        _check_openai()
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra_kwargs = extra_openai_kwargs or {}
        self._client = OpenAI(api_key=api_key) if api_key else OpenAI()

        self.validator = Validator(
            schema=schema,
            llm_callable=self._call_openai,
            max_retries=max_retries,
            retry_strategy=retry_strategy,
            raise_on_failure=raise_on_failure,
            system_prompt=system_prompt,
        )

    # ------------------------------------------------------------------
    # Internal LLM callable
    # ------------------------------------------------------------------

    def _call_openai(self, prompt: str, **kwargs: Any) -> str:
        messages: List[Dict[str, str]] = [{"role": "user", "content": prompt}]
        call_kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            **self.extra_kwargs,
            **kwargs,
        }
        if self.max_tokens is not None:
            call_kwargs["max_tokens"] = self.max_tokens

        try:
            response = self._client.chat.completions.create(**call_kwargs)
            return response.choices[0].message.content or ""
        except Exception as exc:
            raise IntegrationError(
                f"OpenAI API call failed: {exc}",
                integration="openai",
                cause=exc,
            ) from exc

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def guard(self, prompt: str, **kwargs: Any) -> GuardResult:
        return self.validator.guard(prompt, **kwargs)

    def validate_output(self, raw_output: str) -> GuardResult:
        return self.validator.validate_output(raw_output)
