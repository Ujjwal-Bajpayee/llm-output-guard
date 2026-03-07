"""Tests for the core Validator."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from llm_output_guard import GuardResult, ValidationError, Validator
from llm_output_guard.core.exceptions import MaxRetriesExceededError


class TestValidatorBasic:
    def test_successful_validation_json_schema(self, person_json_schema, mock_llm):
        v = Validator(schema=person_json_schema, llm_callable=mock_llm)
        result = v.guard("Who is Alice?")
        assert result.success is True
        assert result.data == {"name": "Alice", "age": 30}
        assert result.attempts == 1

    def test_validate_output_no_llm(self, person_json_schema):
        v = Validator(schema=person_json_schema)
        result = v.validate_output('{"name": "Alice", "age": 30}')
        assert result.success is True

    def test_validate_output_failure(self, person_json_schema):
        v = Validator(schema=person_json_schema)
        result = v.validate_output('{"name": "Alice"}')
        assert result.success is False
        assert result.errors

    def test_guard_without_llm_raises(self, person_json_schema):
        v = Validator(schema=person_json_schema)
        with pytest.raises(ValueError, match="No llm_callable"):
            v.guard("test prompt")

    def test_guard_result_raise_for_status_success(self, person_json_schema, mock_llm):
        v = Validator(schema=person_json_schema, llm_callable=mock_llm)
        result = v.guard("test")
        assert result.raise_for_status() is result

    def test_guard_result_raise_for_status_failure(self, person_json_schema):
        v = Validator(schema=person_json_schema)
        result = v.validate_output('{"name": "Alice"}')
        with pytest.raises(ValidationError):
            result.raise_for_status()


class TestValidatorRetry:
    def test_retries_on_failure(self, person_json_schema):
        call_count = 0

        def llm(prompt: str, **kwargs) -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return "not json"
            return '{"name": "Alice", "age": 30}'

        with patch("time.sleep"):  # Don't actually sleep in tests
            v = Validator(schema=person_json_schema, llm_callable=llm, max_retries=3)
            result = v.guard("test")

        assert result.success is True
        assert call_count == 3

    def test_max_retries_exceeded_returns_failed_result(self, person_json_schema, failing_llm):
        with patch("time.sleep"):
            v = Validator(
                schema=person_json_schema,
                llm_callable=failing_llm,
                max_retries=2,
                raise_on_failure=False,
            )
            result = v.guard("test")

        assert result.success is False
        assert result.attempts == 3

    def test_max_retries_exceeded_raises(self, person_json_schema, failing_llm):
        with patch("time.sleep"):
            v = Validator(
                schema=person_json_schema,
                llm_callable=failing_llm,
                max_retries=2,
                raise_on_failure=True,
            )
            with pytest.raises(MaxRetriesExceededError) as exc_info:
                v.guard("test")
        assert exc_info.value.attempts == 3


class TestValidatorJSONExtraction:
    def test_extracts_json_from_markdown_fence(self, person_json_schema):
        def llm(prompt: str, **kwargs) -> str:
            return '```json\n{"name": "Alice", "age": 30}\n```'

        v = Validator(schema=person_json_schema, llm_callable=llm)
        result = v.guard("test")
        assert result.success is True
        assert result.data["name"] == "Alice"

    def test_extracts_json_from_prose(self, person_json_schema):
        def llm(prompt: str, **kwargs) -> str:
            return 'Here is the data: {"name": "Alice", "age": 30} as requested.'

        v = Validator(schema=person_json_schema, llm_callable=llm)
        result = v.guard("test")
        assert result.success is True

    def test_strict_json_fails_on_prose(self, person_json_schema):
        def llm(prompt: str, **kwargs) -> str:
            return 'Here is: {"name": "Alice", "age": 30}'

        v = Validator(schema=person_json_schema, llm_callable=llm, strict_json=True, max_retries=0)
        result = v.guard("test")
        assert result.success is False


class TestGuardResult:
    def test_error_summary_empty(self):
        r = GuardResult(success=True, data={}, raw_output="")
        assert r.error_summary == "No errors."

    def test_error_summary_with_errors(self):
        r = GuardResult(
            success=False,
            data=None,
            raw_output="",
            errors=[{"loc": ["age"], "msg": "field required"}],
        )
        assert "age" in r.error_summary
        assert "field required" in r.error_summary
