"""Shared fixtures and configuration for the test suite."""

from __future__ import annotations

from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

try:
    from pydantic import BaseModel
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

if PYDANTIC_AVAILABLE:
    class PersonModel(BaseModel):
        name: str
        age: int

    class AddressModel(BaseModel):
        street: str
        city: str
        country: str

    class PersonWithAddress(BaseModel):
        name: str
        age: int
        address: AddressModel
else:
    PersonModel = None  # type: ignore
    AddressModel = None  # type: ignore
    PersonWithAddress = None  # type: ignore


# ---------------------------------------------------------------------------
# JSON Schema fixtures
# ---------------------------------------------------------------------------

PERSON_JSON_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
    },
    "required": ["name", "age"],
}

ARTICLE_JSON_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "content": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "content"],
}


# ---------------------------------------------------------------------------
# Plain dict schema fixtures
# ---------------------------------------------------------------------------

PERSON_DICT_SCHEMA: Dict[str, Any] = {
    "name": str,
    "age": int,
}


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def person_pydantic_model():
    if not PYDANTIC_AVAILABLE:
        pytest.skip("Pydantic not installed")
    return PersonModel


@pytest.fixture
def person_json_schema():
    return PERSON_JSON_SCHEMA


@pytest.fixture
def person_dict_schema():
    return PERSON_DICT_SCHEMA


@pytest.fixture
def valid_person_dict():
    return {"name": "Alice", "age": 30}


@pytest.fixture
def invalid_person_dict():
    return {"name": "Bob"}  # Missing 'age'


@pytest.fixture
def mock_llm():
    """Return a mock LLM callable."""
    mock = MagicMock()
    mock.return_value = '{"name": "Alice", "age": 30}'
    return mock


@pytest.fixture
def failing_llm():
    """LLM that always returns invalid JSON."""
    mock = MagicMock()
    mock.return_value = "Sorry, I cannot answer that."
    return mock
