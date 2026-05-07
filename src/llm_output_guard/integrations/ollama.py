"""Ollama integration for llm-output-guard."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from ..core.exceptions import IntegrationError
from ..core.validator import GuardResult, Validator

if TYPE_CHECKING:
    from ..core.types import SchemaDefinition

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


def _check_requests() -> None:
    if not REQUESTS_AVAILABLE:
        raise IntegrationError(
            "requests library is not installed. Run: pip install requests",
            integration="ollama",
        )


class GuardedOllama:
    """
    Convenience wrapper that creates a :class:`~llm_output_guard.Validator`
    pre-wired to a local Ollama instance.

    Usage::

        from llm_output_guard.integrations.ollama import GuardedOllama

        guard = GuardedOllama(
            schema=MyPydanticModel,
            model="mistral",
        )
        result = guard.guard("Summarise the following article: ...")
        print(result.data)

    Configuration via environment variables::

        OLLAMA_BASE_URL=http://localhost:11434  # Default if not set
        OLLAMA_MODEL=mistral  # Optional, can be overridden in code
    """

    def __init__(
        self,
        schema: SchemaDefinition,
        *,
        model: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
        max_retries: int = 2,
        retry_strategy: str = "exponential",
        raise_on_failure: bool = False,
        system_prompt: str | None = None,
        extra_ollama_kwargs: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> None:
        _check_requests()

        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL")
        if not self.model:
            raise IntegrationError(
                "Model name must be provided via 'model' parameter or OLLAMA_MODEL environment variable",
                integration="ollama",
            )

        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.extra_kwargs = extra_ollama_kwargs or {}

        self.validator = Validator(
            schema=schema,
            llm_callable=self._call_ollama,
            max_retries=max_retries,
            retry_strategy=retry_strategy,
            raise_on_failure=raise_on_failure,
            system_prompt=system_prompt,
        )

    # ------------------------------------------------------------------
    # Internal LLM callable
    # ------------------------------------------------------------------

    def _call_ollama(self, prompt: str, **kwargs: Any) -> str:
        url = f"{self.base_url}/api/generate"

        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "temperature": self.temperature,
            "stream": False,
            **self.extra_kwargs,
            **kwargs,
        }

        if self.max_tokens is not None:
            payload["num_predict"] = self.max_tokens

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()

            if "response" not in result:
                raise IntegrationError(
                    f"Unexpected Ollama response format: {result}",
                    integration="ollama",
                )

            response_text = result["response"]
            if not isinstance(response_text, str):
                raise IntegrationError(
                    f"Expected string response, got {type(response_text).__name__}",
                    integration="ollama",
                )
            return response_text

        except requests.exceptions.ConnectionError as exc:
            raise IntegrationError(
                f"Failed to connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running and accessible.",
                integration="ollama",
                cause=exc,
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise IntegrationError(
                f"Ollama request timed out after {self.timeout} seconds",
                integration="ollama",
                cause=exc,
            ) from exc
        except requests.exceptions.HTTPError as exc:
            raise IntegrationError(
                f"Ollama API error: {exc.response.status_code} - {exc.response.text}",
                integration="ollama",
                cause=exc,
            ) from exc
        except Exception as exc:
            raise IntegrationError(
                f"Ollama API call failed: {exc}",
                integration="ollama",
                cause=exc,
            ) from exc

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def guard(self, prompt: str, **kwargs: Any) -> GuardResult:
        return self.validator.guard(prompt, **kwargs)

    def validate_output(self, raw_output: str) -> GuardResult:
        return self.validator.validate_output(raw_output)
