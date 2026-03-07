"""Schema fixtures shared across the test suite."""

from __future__ import annotations

from typing import Any

try:
    from pydantic import BaseModel, Field

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False


# ---------------------------------------------------------------------------
# Pydantic models (only defined when Pydantic is available)
# ---------------------------------------------------------------------------

if PYDANTIC_AVAILABLE:

    class PersonModel(BaseModel):
        name: str
        age: int

    class ArticleModel(BaseModel):
        title: str
        content: str
        tags: list[str] = Field(default_factory=list)

    class NestedAddressModel(BaseModel):
        street: str
        city: str
        zip_code: str | None = None

    class UserProfileModel(BaseModel):
        username: str
        email: str
        address: NestedAddressModel
        active: bool = True


# ---------------------------------------------------------------------------
# JSON Schema dicts
# ---------------------------------------------------------------------------

PERSON_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft-07/schema",
    "type": "object",
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "age": {"type": "integer", "minimum": 0},
    },
    "required": ["name", "age"],
    "additionalProperties": False,
}

ARTICLE_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "content": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "content"],
}

FLEXIBLE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "result": {},
        "confidence": {"type": "number"},
    },
    "required": ["result"],
}


# ---------------------------------------------------------------------------
# Plain dict schemas
# ---------------------------------------------------------------------------

PERSON_DICT_SCHEMA: dict[str, Any] = {
    "name": str,
    "age": int,
}

MIXED_DICT_SCHEMA: dict[str, Any] = {
    "name": ...,  # required, any type
    "score": float,
}
