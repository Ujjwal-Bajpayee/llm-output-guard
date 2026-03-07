"""
llm-output-guard
~~~~~~~~~~~~~~~~

A production-ready library for validating LLM outputs against schemas,
with automatic retry and JSON extraction.

Basic usage::

    from llm_output_guard import Validator
    from pydantic import BaseModel

    class Person(BaseModel):
        name: str
        age: int

    def my_llm(prompt: str) -> str:
        # Replace with your actual LLM call
        return '{"name": "Alice", "age": 30}'

    validator = Validator(schema=Person, llm_callable=my_llm)
    result = validator.guard("Tell me about Alice.")
    print(result.data)        # Person(name='Alice', age=30)
    print(result.success)     # True

See https://github.com/Ujjwal-Bajpayee/llm-output-guard for full documentation.
"""

from .__version__ import __version__, __version_info__
from .core.exceptions import (
    IntegrationError,
    JSONParseError,
    LLMOutputGuardError,
    MaxRetriesExceededError,
    SchemaParseError,
    ValidationError,
)
from .core.schema_parser import SchemaParser
from .core.types import RetryStrategy, SchemaType
from .core.validator import GuardResult, Validator

__all__ = [
    # Primary API
    "Validator",
    "GuardResult",
    "SchemaParser",
    # Enumerations
    "SchemaType",
    "RetryStrategy",
    # Exceptions
    "LLMOutputGuardError",
    "ValidationError",
    "SchemaParseError",
    "JSONParseError",
    "MaxRetriesExceededError",
    "IntegrationError",
    # Version
    "__version__",
    "__version_info__",
]
