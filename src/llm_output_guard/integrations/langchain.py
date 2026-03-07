"""LangChain integration for llm-output-guard."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type

from ..core.exceptions import IntegrationError
from ..core.types import SchemaDefinition
from ..core.validator import GuardResult, Validator

try:
    from langchain_core.language_models import BaseLanguageModel
    from langchain_core.messages import HumanMessage
    from langchain_core.output_parsers import BaseOutputParser
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        from langchain.schema import BaseLanguageModel, HumanMessage
        from langchain.schema import BaseOutputParser
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False


def _check_langchain() -> None:
    if not LANGCHAIN_AVAILABLE:
        raise IntegrationError(
            "LangChain is not installed. Run: pip install langchain-core",
            integration="langchain",
        )


class GuardedLLM:
    """
    Wraps a LangChain LLM and validates its output against *schema*.

    Usage::

        from langchain_openai import ChatOpenAI
        from llm_output_guard.integrations.langchain import GuardedLLM

        llm = ChatOpenAI(model="gpt-4o-mini")
        guarded = GuardedLLM(llm=llm, schema=MyModel)
        result = guarded.invoke("Extract the key facts from: ...")
        print(result.data)
    """

    def __init__(
        self,
        llm: Any,
        schema: SchemaDefinition,
        *,
        max_retries: int = 2,
        retry_strategy: str = "exponential",
        raise_on_failure: bool = False,
    ) -> None:
        _check_langchain()
        self._llm = llm
        self.validator = Validator(
            schema=schema,
            llm_callable=self._call_llm,
            max_retries=max_retries,
            retry_strategy=retry_strategy,
            raise_on_failure=raise_on_failure,
        )

    def _call_llm(self, prompt: str, **kwargs: Any) -> str:
        """Invoke the underlying LangChain LLM and return its string output."""
        try:
            response = self._llm.invoke(prompt, **kwargs)
            if hasattr(response, "content"):
                return response.content
            return str(response)
        except Exception as exc:
            raise IntegrationError(
                f"LangChain LLM invocation failed: {exc}",
                integration="langchain",
                cause=exc,
            ) from exc

    def invoke(self, prompt: str, **kwargs: Any) -> GuardResult:
        return self.validator.guard(prompt, **kwargs)


class GuardOutputParser:
    """
    A LangChain-compatible output parser that validates JSON against *schema*.

    Can be used directly in LCEL chains::

        chain = prompt | llm | GuardOutputParser(schema=MyModel)
        result = chain.invoke({"topic": "AI"})
    """

    def __init__(self, schema: SchemaDefinition) -> None:
        _check_langchain()
        from ..core.schema_parser import SchemaParser
        self._parser = SchemaParser(schema)
        from ..utils.json_helpers import extract_json
        self._extract_json = extract_json

    def parse(self, text: str) -> Any:
        data = self._extract_json(text)
        result, errors = self._parser.validate(data)
        if errors:
            from ..core.exceptions import ValidationError
            raise ValidationError(
                "Output does not match schema.",
                errors=errors,
                raw_output=text,
            )
        return result

    def get_format_instructions(self) -> str:
        return (
            "Return a JSON object matching this schema:\n"
            + self._parser.describe()
        )
