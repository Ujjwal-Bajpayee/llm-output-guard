"""Type definitions for llm-output-guard."""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Optional, Union

try:
    from pydantic import BaseModel as PydanticBaseModel

    PYDANTIC_AVAILABLE = True
except ImportError:
    PydanticBaseModel = None  # type: ignore
    PYDANTIC_AVAILABLE = False


class SchemaType(str, Enum):
    """Supported schema types."""

    PYDANTIC = "pydantic"
    JSON_SCHEMA = "json_schema"
    DICT = "dict"


class RetryStrategy(str, Enum):
    """Retry strategies."""

    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"


# Type alias for schema definitions
SchemaDefinition = Union[
    type["PydanticBaseModel"],
    dict[str, Any],
    list[Any],
]

# Type alias for LLM callable
LLMCallable = Callable[..., str]

# Type alias for validation result
ValidationResult = dict[str, Any]

# Type alias for parsed output
ParsedOutput = Optional[dict[str, Any]]
