"""Tests for utility functions: json_helpers and validators."""

from __future__ import annotations

import pytest

from llm_output_guard.core.exceptions import JSONParseError
from llm_output_guard.utils.json_helpers import extract_json, parse_json_safely, to_json_string
from llm_output_guard.utils.validators import (
    is_non_empty_list,
    is_non_empty_string,
    is_positive_number,
    is_valid_email,
    is_valid_url,
    validate_fields,
)

# ---------------------------------------------------------------------------
# parse_json_safely
# ---------------------------------------------------------------------------


class TestParseJsonSafely:
    def test_valid_object(self):
        assert parse_json_safely('{"a": 1}') == {"a": 1}

    def test_valid_array(self):
        assert parse_json_safely("[1, 2, 3]") == [1, 2, 3]

    def test_whitespace_stripped(self):
        assert parse_json_safely('  {"x": true}  ') == {"x": True}

    def test_invalid_raises(self):
        with pytest.raises(JSONParseError, match="Cannot parse JSON"):
            parse_json_safely("not json at all")

    def test_truncated_raises(self):
        with pytest.raises(JSONParseError):
            parse_json_safely('{"a":')


# ---------------------------------------------------------------------------
# extract_json
# ---------------------------------------------------------------------------


class TestExtractJson:
    def test_plain_json(self):
        assert extract_json('{"name": "Alice"}') == {"name": "Alice"}

    def test_markdown_fence_json(self):
        raw = '```json\n{"name": "Alice"}\n```'
        assert extract_json(raw) == {"name": "Alice"}

    def test_markdown_fence_no_lang(self):
        raw = '```\n{"name": "Alice"}\n```'
        assert extract_json(raw) == {"name": "Alice"}

    def test_prose_wrapped(self):
        raw = 'Sure, here is the result: {"name": "Alice"} — done.'
        result = extract_json(raw)
        assert result["name"] == "Alice"

    def test_array_extraction(self):
        raw = "Output: [1, 2, 3]"
        assert extract_json(raw) == [1, 2, 3]

    def test_single_quoted_repair(self):
        # Best-effort single-quote repair
        result = extract_json("{'name': 'Alice'}")
        assert result["name"] == "Alice"

    def test_no_json_raises(self):
        with pytest.raises(JSONParseError, match="Could not extract"):
            extract_json("No JSON here whatsoever.")

    def test_nested_object(self):
        raw = '{"a": {"b": [1, 2]}}'
        assert extract_json(raw) == {"a": {"b": [1, 2]}}


# ---------------------------------------------------------------------------
# to_json_string
# ---------------------------------------------------------------------------


class TestToJsonString:
    def test_basic_dict(self):
        result = to_json_string({"a": 1})
        assert '"a": 1' in result

    def test_indent_respected(self):
        result = to_json_string({"a": 1}, indent=4)
        assert "    " in result

    def test_non_serialisable_raises(self):
        with pytest.raises(JSONParseError):
            to_json_string(object())


# ---------------------------------------------------------------------------
# Field validators
# ---------------------------------------------------------------------------


class TestIsNonEmptyString:
    def test_valid(self):
        assert is_non_empty_string("hello") is True

    def test_empty_string(self):
        assert is_non_empty_string("") is False

    def test_whitespace_only(self):
        assert is_non_empty_string("   ") is False

    def test_non_string(self):
        assert is_non_empty_string(42) is False


class TestIsPositiveNumber:
    def test_int(self):
        assert is_positive_number(1) is True

    def test_float(self):
        assert is_positive_number(0.5) is True

    def test_zero(self):
        assert is_positive_number(0) is False

    def test_negative(self):
        assert is_positive_number(-1) is False

    def test_string(self):
        assert is_positive_number("5") is False


class TestIsValidEmail:
    def test_valid(self):
        assert is_valid_email("user@example.com") is True

    def test_valid_with_plus(self):
        assert is_valid_email("user+tag@example.co.uk") is True

    def test_missing_at(self):
        assert is_valid_email("userexample.com") is False

    def test_missing_domain(self):
        assert is_valid_email("user@") is False

    def test_non_string(self):
        assert is_valid_email(None) is False


class TestIsValidUrl:
    def test_https(self):
        assert is_valid_url("https://example.com") is True

    def test_http(self):
        assert is_valid_url("http://example.com/path?q=1") is True

    def test_no_scheme(self):
        assert is_valid_url("example.com") is False

    def test_ftp_not_valid(self):
        assert is_valid_url("ftp://example.com") is False

    def test_non_string(self):
        assert is_valid_url(123) is False


class TestIsNonEmptyList:
    def test_non_empty(self):
        assert is_non_empty_list([1, 2]) is True

    def test_empty(self):
        assert is_non_empty_list([]) is False

    def test_non_list(self):
        assert is_non_empty_list("abc") is False


class TestValidateFields:
    def test_passes_when_all_valid(self):
        errors = validate_fields({"email": "a@b.com"}, {"email": [is_valid_email]})
        assert errors == []

    def test_fails_when_invalid(self):
        errors = validate_fields({"email": "bad-email"}, {"email": [is_valid_email]})
        assert len(errors) == 1
        assert errors[0]["loc"] == ["email"]

    def test_multiple_validators_one_fails(self):
        errors = validate_fields(
            {"name": "  "},
            {"name": [is_non_empty_string]},
        )
        assert len(errors) == 1

    def test_missing_field_treated_as_none(self):
        # Missing field → value is None → is_valid_email(None) is False
        errors = validate_fields({}, {"email": [is_valid_email]})
        assert len(errors) == 1
