"""Custom exceptions for llm-output-guard."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class LLMOutputGuardError(Exception):
    """Base exception for all llm-output-guard errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, details={self.details!r})"


class ValidationError(LLMOutputGuardError):
    """Raised when LLM output fails schema validation."""

    def __init__(
        self,
        message: str,
        errors: Optional[List[Dict[str, Any]]] = None,
        raw_output: Optional[str] = None,
        attempts: int = 0,
    ) -> None:
        super().__init__(message, details={"errors": errors or [], "raw_output": raw_output})
        self.errors = errors or []
        self.raw_output = raw_output
        self.attempts = attempts

    @property
    def error_count(self) -> int:
        return len(self.errors)

    def format_errors(self) -> str:
        if not self.errors:
            return "No specific validation errors available."
        lines = [f"Validation failed with {self.error_count} error(s):"]
        for i, err in enumerate(self.errors, 1):
            loc = " -> ".join(str(x) for x in err.get("loc", []))
            msg = err.get("msg", "Unknown error")
            lines.append(f"  {i}. [{loc}] {msg}" if loc else f"  {i}. {msg}")
        return "\n".join(lines)


class SchemaParseError(LLMOutputGuardError):
    """Raised when the provided schema cannot be parsed."""

    def __init__(
        self, message: str, schema: Any = None, schema_type: Optional[str] = None
    ) -> None:
        super().__init__(message, details={"schema": str(schema), "schema_type": schema_type})
        self.schema = schema
        self.schema_type = schema_type


class JSONParseError(LLMOutputGuardError):
    """Raised when LLM output cannot be parsed as JSON."""

    def __init__(self, message: str, raw_output: Optional[str] = None) -> None:
        super().__init__(message, details={"raw_output": raw_output})
        self.raw_output = raw_output


class MaxRetriesExceededError(LLMOutputGuardError):
    """Raised when the maximum number of retry attempts is exceeded."""

    def __init__(
        self,
        message: str,
        attempts: int = 0,
        last_error: Optional[Exception] = None,
    ) -> None:
        super().__init__(
            message, details={"attempts": attempts, "last_error": str(last_error)}
        )
        self.attempts = attempts
        self.last_error = last_error


class IntegrationError(LLMOutputGuardError):
    """Raised when an integration (LangChain, FastAPI, etc.) encounters an error."""

    def __init__(
        self, message: str, integration: Optional[str] = None, cause: Optional[Exception] = None
    ) -> None:
        super().__init__(message, details={"integration": integration, "cause": str(cause)})
        self.integration = integration
        self.cause = cause
