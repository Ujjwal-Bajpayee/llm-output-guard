"""Core Validator — the primary public interface of llm-output-guard."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

from .exceptions import (
    JSONParseError,
    MaxRetriesExceededError,
    ValidationError,
)
from .schema_parser import SchemaParser
from .types import LLMCallable, SchemaDefinition

logger = logging.getLogger(__name__)


@dataclass
class GuardResult:
    """
    Encapsulates the outcome of a single guard call.

    Attributes:
        success:        ``True`` when validation passed.
        data:           The validated (and possibly coerced) output, or ``None``.
        raw_output:     The raw string returned by the LLM.
        errors:         List of validation error dicts (empty on success).
        attempts:       Total number of LLM calls made.
        schema_type:    The schema type that was used (``"pydantic"``, etc.).
    """

    success: bool
    data: Optional[Any]
    raw_output: str
    errors: List[Dict[str, Any]] = field(default_factory=list)
    attempts: int = 1
    schema_type: str = ""

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def raise_for_status(self) -> "GuardResult":
        """Raise :exc:`ValidationError` if validation failed, else return self."""
        if not self.success:
            raise ValidationError(
                message="LLM output failed schema validation.",
                errors=self.errors,
                raw_output=self.raw_output,
                attempts=self.attempts,
            )
        return self

    @property
    def error_summary(self) -> str:
        if not self.errors:
            return "No errors."
        lines = [f"{len(self.errors)} validation error(s):"]
        for err in self.errors:
            loc = " -> ".join(str(x) for x in err.get("loc", []))
            msg = err.get("msg", "?")
            lines.append(f"  • [{loc}] {msg}" if loc else f"  • {msg}")
        return "\n".join(lines)


class Validator:
    """
    Validate LLM outputs against a schema, with automatic JSON extraction and
    optional retry logic.

    Basic usage::

        from llm_output_guard import Validator

        class Person(BaseModel):
            name: str
            age: int

        validator = Validator(schema=Person, llm_callable=my_llm)
        result = validator.guard("Who is Alice?")
        print(result.data)

    Parameters:
        schema:           A Pydantic model class, JSON Schema dict, or plain dict.
        llm_callable:     A callable ``(prompt: str, **kwargs) -> str``.
        max_retries:      How many times to retry on failure (default ``2``).
        retry_strategy:   ``"fixed"`` | ``"exponential"`` | ``"linear"``.
        retry_delay:      Base delay (seconds) between retries (default ``1.0``).
        raise_on_failure: If ``True``, raise :exc:`ValidationError` after all
                          retries are exhausted instead of returning a failed
                          :class:`GuardResult` (default ``False``).
        strict_json:      Require the entire response to be valid JSON; don't
                          attempt to extract a JSON block (default ``False``).
        system_prompt:    Optional system-level instructions prepended to every
                          prompt.
    """

    def __init__(
        self,
        schema: SchemaDefinition,
        llm_callable: Optional[LLMCallable] = None,
        *,
        max_retries: int = 2,
        retry_strategy: str = "exponential",
        retry_delay: float = 1.0,
        raise_on_failure: bool = False,
        strict_json: bool = False,
        system_prompt: Optional[str] = None,
    ) -> None:
        self.schema_parser = SchemaParser(schema)
        self.llm_callable = llm_callable
        self.max_retries = max_retries
        self.retry_strategy = retry_strategy
        self.retry_delay = retry_delay
        self.raise_on_failure = raise_on_failure
        self.strict_json = strict_json
        self.system_prompt = system_prompt

        # Import lazily to avoid circular imports
        from ..retry.manager import RetryManager
        from ..utils.json_helpers import extract_json, parse_json_safely
        from ..utils.prompt_builder import build_validation_prompt

        self._retry_manager = RetryManager(
            max_retries=max_retries,
            strategy=retry_strategy,
            base_delay=retry_delay,
        )
        self._extract_json = extract_json
        self._parse_json = parse_json_safely
        self._build_prompt = build_validation_prompt

    # ------------------------------------------------------------------
    # Primary entry-points
    # ------------------------------------------------------------------

    def guard(self, prompt: str, **llm_kwargs: Any) -> GuardResult:
        """
        Call the LLM with *prompt* and validate the response against the schema.

        Retries automatically on validation or JSON-parse failures.

        Raises:
            MaxRetriesExceededError: when ``raise_on_failure=True`` and all
                attempts fail.
        """
        if self.llm_callable is None:
            raise ValueError(
                "No llm_callable provided. Either pass it to the constructor "
                "or use validate_output() to validate an existing string."
            )

        augmented_prompt = self._build_prompt(
            prompt=prompt,
            schema_description=self.schema_parser.describe(),
            system_prompt=self.system_prompt,
        )

        attempts = 0
        last_result: Optional[GuardResult] = None
        last_raw = ""
        current_prompt = augmented_prompt

        for attempt_num in range(1, self.max_retries + 2):
            attempts = attempt_num
            try:
                raw = self.llm_callable(current_prompt, **llm_kwargs)
                last_raw = raw
                result = self._process_response(raw, attempts=attempts)
                if result.success:
                    logger.debug("Validation succeeded on attempt %d.", attempts)
                    return result
                last_result = result
                logger.debug(
                    "Attempt %d failed validation: %s", attempts, result.error_summary
                )
            except (JSONParseError, ValidationError) as exc:
                last_result = GuardResult(
                    success=False,
                    data=None,
                    raw_output=last_raw,
                    errors=[{"msg": str(exc)}],
                    attempts=attempts,
                    schema_type=self.schema_parser.schema_type.value,
                )

            if attempt_num <= self.max_retries:
                self._retry_manager.wait(attempt_num)
                current_prompt = self._build_prompt(
                    prompt=prompt,
                    schema_description=self.schema_parser.describe(),
                    system_prompt=self.system_prompt,
                    previous_errors=(last_result.errors if last_result else []),
                )

        if self.raise_on_failure:
            raise MaxRetriesExceededError(
                f"Validation failed after {attempts} attempt(s).",
                attempts=attempts,
                last_error=ValidationError(
                    "Max retries exceeded.",
                    errors=last_result.errors if last_result else [],
                    raw_output=last_raw,
                ),
            )

        assert last_result is not None
        return last_result

    def validate_output(self, raw_output: str) -> GuardResult:
        """
        Validate an *existing* LLM output string without calling the LLM.

        Useful when you already have the raw string and just want schema
        validation + JSON parsing.
        """
        return self._process_response(raw_output, attempts=1)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _process_response(self, raw: str, *, attempts: int) -> GuardResult:
        schema_type = self.schema_parser.schema_type.value

        # 1. Parse JSON
        try:
            if self.strict_json:
                data = self._parse_json(raw)
            else:
                data = self._extract_json(raw)
        except JSONParseError as exc:
            return GuardResult(
                success=False,
                data=None,
                raw_output=raw,
                errors=[{"msg": f"JSON parse error: {exc}"}],
                attempts=attempts,
                schema_type=schema_type,
            )

        # 2. Schema validation
        validated, errors = self.schema_parser.validate(data)
        if errors:
            return GuardResult(
                success=False,
                data=None,
                raw_output=raw,
                errors=errors,
                attempts=attempts,
                schema_type=schema_type,
            )

        return GuardResult(
            success=True,
            data=validated,
            raw_output=raw,
            errors=[],
            attempts=attempts,
            schema_type=schema_type,
        )
