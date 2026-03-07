"""Additional tests for integration modules and exceptions module."""

from __future__ import annotations

import pytest

from llm_output_guard.core.exceptions import (
    JSONParseError,
    LLMOutputGuardError,
    MaxRetriesExceededError,
    SchemaParseError,
    ValidationError,
    IntegrationError,
)


# ---------------------------------------------------------------------------
# Exception classes
# ---------------------------------------------------------------------------

class TestExceptions:
    def test_base_error_message(self):
        e = LLMOutputGuardError("test error")
        assert str(e) == "test error"
        assert e.message == "test error"
        assert e.details == {}

    def test_base_error_with_details(self):
        e = LLMOutputGuardError("msg", details={"key": "val"})
        assert e.details["key"] == "val"

    def test_validation_error_format(self):
        e = ValidationError(
            "bad output",
            errors=[{"loc": ["name"], "msg": "field required"}],
            raw_output="{}",
            attempts=2,
        )
        assert e.error_count == 1
        assert e.attempts == 2
        assert "name" in e.format_errors()

    def test_validation_error_no_errors(self):
        e = ValidationError("failed")
        assert e.error_count == 0
        assert "No specific" in e.format_errors()

    def test_schema_parse_error(self):
        e = SchemaParseError("bad schema", schema="x", schema_type="dict")
        assert e.schema == "x"
        assert e.schema_type == "dict"

    def test_json_parse_error(self):
        e = JSONParseError("invalid json", raw_output="foo")
        assert e.raw_output == "foo"

    def test_max_retries_error(self):
        inner = ValueError("original")
        e = MaxRetriesExceededError("exceeded", attempts=3, last_error=inner)
        assert e.attempts == 3
        assert e.last_error is inner

    def test_integration_error(self):
        cause = RuntimeError("api down")
        e = IntegrationError("failed", integration="openai", cause=cause)
        assert e.integration == "openai"
        assert e.cause is cause

    def test_repr(self):
        e = LLMOutputGuardError("msg", details={"x": 1})
        r = repr(e)
        assert "LLMOutputGuardError" in r
        assert "msg" in r


# ---------------------------------------------------------------------------
# LangChain GuardOutputParser (no real LLM needed)
# ---------------------------------------------------------------------------

class TestGuardOutputParserUnit:
    def test_parse_valid(self):
        from llm_output_guard.integrations.langchain import GuardOutputParser, LANGCHAIN_AVAILABLE
        if not LANGCHAIN_AVAILABLE:
            pytest.skip("LangChain not installed")
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        parser = GuardOutputParser(schema=schema)
        result = parser.parse('{"name": "Alice"}')
        assert result == {"name": "Alice"}

    def test_parse_invalid_raises(self):
        from llm_output_guard.integrations.langchain import GuardOutputParser, LANGCHAIN_AVAILABLE
        if not LANGCHAIN_AVAILABLE:
            pytest.skip("LangChain not installed")
        from llm_output_guard.core.exceptions import ValidationError
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        parser = GuardOutputParser(schema=schema)
        with pytest.raises(ValidationError):
            parser.parse('{"age": 30}')

    def test_get_format_instructions(self):
        from llm_output_guard.integrations.langchain import GuardOutputParser, LANGCHAIN_AVAILABLE
        if not LANGCHAIN_AVAILABLE:
            pytest.skip("LangChain not installed")
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        parser = GuardOutputParser(schema=schema)
        instructions = parser.get_format_instructions()
        assert "JSON" in instructions
        assert "name" in instructions


# ---------------------------------------------------------------------------
# FastAPI guarded_endpoint (smoke test; no HTTP call needed)
# ---------------------------------------------------------------------------

class TestFastAPIIntegration:
    def test_import_without_fastapi(self):
        import llm_output_guard.integrations.fastapi as fa_mod
        original = fa_mod.FASTAPI_AVAILABLE
        fa_mod.FASTAPI_AVAILABLE = False
        try:
            with pytest.raises(IntegrationError, match="FastAPI"):
                fa_mod.guarded_endpoint(schema={}, llm_callable=lambda p: p)
        finally:
            fa_mod.FASTAPI_AVAILABLE = original

    def test_guarded_endpoint_decorator_is_callable(self):
        """guarded_endpoint returns a decorator without raising."""
        from llm_output_guard.integrations.fastapi import FASTAPI_AVAILABLE, guarded_endpoint
        if not FASTAPI_AVAILABLE:
            pytest.skip("FastAPI not installed")

        schema = {
            "type": "object",
            "properties": {"result": {"type": "string"}},
            "required": ["result"],
        }

        def fake_llm(prompt: str, **kwargs) -> str:
            return '{"result": "ok"}'

        decorator = guarded_endpoint(schema=schema, llm_callable=fake_llm, max_retries=0)
        assert callable(decorator)

        # Apply the decorator to a plain async function and verify it wraps correctly
        import asyncio

        async def route_fn():
            return '{"result": "ok"}'

        wrapped = decorator(route_fn)
        assert callable(wrapped)
        assert wrapped.__name__ == "route_fn"

    def test_llm_guard_middleware_init(self):
        from llm_output_guard.integrations.fastapi import LLMGuardMiddleware, FASTAPI_AVAILABLE
        if not FASTAPI_AVAILABLE:
            pytest.skip("FastAPI not installed")
        from fastapi import FastAPI
        app = FastAPI()
        schema = {"type": "object", "properties": {"x": {"type": "string"}}}
        mw = LLMGuardMiddleware(app=app, schema=schema)
        assert mw.app is app


# ---------------------------------------------------------------------------
# OpenAI guard — validate_output path (no API call)
# ---------------------------------------------------------------------------

class TestGuardedOpenAIUnit:
    def test_validate_output_success(self):
        from llm_output_guard.integrations.openai import GuardedOpenAI, OPENAI_AVAILABLE
        if not OPENAI_AVAILABLE:
            pytest.skip("OpenAI SDK not installed")
        from unittest.mock import patch
        schema = {
            "type": "object",
            "properties": {"title": {"type": "string"}},
            "required": ["title"],
        }
        with patch("openai.OpenAI"):
            guard = GuardedOpenAI(schema=schema, api_key="sk-fake")
            result = guard.validate_output('{"title": "Hello"}')
        assert result.success is True
        assert result.data["title"] == "Hello"

    def test_validate_output_failure(self):
        from llm_output_guard.integrations.openai import GuardedOpenAI, OPENAI_AVAILABLE
        if not OPENAI_AVAILABLE:
            pytest.skip("OpenAI SDK not installed")
        from unittest.mock import patch
        schema = {
            "type": "object",
            "properties": {"title": {"type": "string"}},
            "required": ["title"],
        }
        with patch("openai.OpenAI"):
            guard = GuardedOpenAI(schema=schema, api_key="sk-fake")
            result = guard.validate_output('{"body": "no title here"}')
        assert result.success is False
