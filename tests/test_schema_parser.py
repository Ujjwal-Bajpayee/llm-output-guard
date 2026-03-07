"""Tests for SchemaParser."""

from __future__ import annotations

from typing import Any

import pytest

from llm_output_guard.core.exceptions import SchemaParseError
from llm_output_guard.core.schema_parser import SchemaParser, detect_schema_type
from llm_output_guard.core.types import SchemaType

PERSON_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
    },
    "required": ["name", "age"],
}


class TestDetectSchemaType:
    def test_detects_json_schema(self):
        assert detect_schema_type(PERSON_JSON_SCHEMA) == SchemaType.JSON_SCHEMA

    def test_detects_dict_schema(self):
        schema = {"name": str, "age": int}
        assert detect_schema_type(schema) == SchemaType.DICT

    def test_detects_pydantic(self, person_pydantic_model):
        assert detect_schema_type(person_pydantic_model) == SchemaType.PYDANTIC

    def test_raises_on_unknown_type(self):
        with pytest.raises(SchemaParseError):
            detect_schema_type("not a schema")  # type: ignore


class TestSchemaParserJSONSchema:
    def test_valid_data_passes(self):
        parser = SchemaParser(PERSON_JSON_SCHEMA)
        result, errors = parser.validate({"name": "Alice", "age": 30})
        assert errors == []
        assert result == {"name": "Alice", "age": 30}

    def test_invalid_data_returns_errors(self):
        parser = SchemaParser(PERSON_JSON_SCHEMA)
        result, errors = parser.validate({"name": "Bob"})
        assert result is None
        assert len(errors) > 0

    def test_json_schema_property(self):
        parser = SchemaParser(PERSON_JSON_SCHEMA)
        assert parser.json_schema == PERSON_JSON_SCHEMA

    def test_describe_returns_string(self):
        parser = SchemaParser(PERSON_JSON_SCHEMA)
        description = parser.describe()
        assert "name" in description


class TestSchemaParserDict:
    def test_valid_data_passes(self):
        schema = {"name": str, "age": int}
        parser = SchemaParser(schema)
        result, errors = parser.validate({"name": "Alice", "age": 30})
        assert errors == []

    def test_missing_key_no_error_when_optional(self):
        schema = {"name": str}  # age is not required in dict schema
        parser = SchemaParser(schema)
        result, errors = parser.validate({"name": "Alice"})
        assert errors == []

    def test_wrong_type_returns_error(self):
        schema = {"age": int}
        parser = SchemaParser(schema)
        result, errors = parser.validate({"age": "thirty"})
        assert len(errors) > 0
        assert errors[0]["type"] == "type_error"

    def test_required_field_missing(self):
        schema = {"name": ...}
        parser = SchemaParser(schema)
        result, errors = parser.validate({})
        assert any(e.get("type") == "missing" for e in errors)


class TestSchemaParserPydantic:
    def test_valid_data_passes(self, person_pydantic_model):
        parser = SchemaParser(person_pydantic_model)
        result, errors = parser.validate({"name": "Alice", "age": 30})
        assert errors == []
        assert result.name == "Alice"
        assert result.age == 30

    def test_invalid_data_returns_errors(self, person_pydantic_model):
        parser = SchemaParser(person_pydantic_model)
        result, errors = parser.validate({"name": "Bob"})
        assert result is None
        assert len(errors) > 0

    def test_json_schema_roundtrip(self, person_pydantic_model):
        parser = SchemaParser(person_pydantic_model)
        js = parser.json_schema
        assert "properties" in js
        assert "name" in js["properties"]
