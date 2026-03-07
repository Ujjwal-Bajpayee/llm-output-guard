"""Tests for third-party integrations."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from llm_output_guard.core.exceptions import IntegrationError


class TestLangChainIntegration:
    def test_import_without_langchain(self):
        """GuardedLLM raises IntegrationError when LangChain is absent."""
        import sys

        # Temporarily hide langchain
        with patch.dict(sys.modules, {"langchain_core": None, "langchain": None}):
            # Force re-evaluation of LANGCHAIN_AVAILABLE
            import llm_output_guard.integrations.langchain as lc_mod

            original = lc_mod.LANGCHAIN_AVAILABLE
            lc_mod.LANGCHAIN_AVAILABLE = False
            try:
                with pytest.raises(IntegrationError, match="LangChain"):
                    lc_mod.GuardedLLM(llm=MagicMock(), schema={"type": "object"})
            finally:
                lc_mod.LANGCHAIN_AVAILABLE = original

    def test_guarded_llm_invokes_llm(self):
        """GuardedLLM.invoke calls the underlying LLM and validates output."""
        from llm_output_guard.integrations.langchain import LANGCHAIN_AVAILABLE, GuardedLLM

        if not LANGCHAIN_AVAILABLE:
            pytest.skip("LangChain not installed")

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content='{"name": "Alice", "age": 30}')
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            "required": ["name", "age"],
        }

        with patch("time.sleep"):
            guarded = GuardedLLM(llm=mock_llm, schema=schema, max_retries=0)
            result = guarded.invoke("test")

        assert result.success is True


class TestOpenAIIntegration:
    def test_import_without_openai(self):
        """GuardedOpenAI raises IntegrationError when openai is absent."""
        import llm_output_guard.integrations.openai as oi_mod

        original = oi_mod.OPENAI_AVAILABLE
        oi_mod.OPENAI_AVAILABLE = False
        try:
            with pytest.raises(IntegrationError, match="OpenAI"):
                oi_mod.GuardedOpenAI(schema={"type": "object"})
        finally:
            oi_mod.OPENAI_AVAILABLE = original

    def test_validate_output_without_api_call(self):
        """validate_output works without making an API call."""
        from llm_output_guard.integrations.openai import OPENAI_AVAILABLE, GuardedOpenAI

        if not OPENAI_AVAILABLE:
            pytest.skip("OpenAI SDK not installed")

        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        with patch("openai.OpenAI"):
            guard = GuardedOpenAI(schema=schema, api_key="sk-fake")
            result = guard.validate_output('{"name": "Alice"}')

        assert result.success is True
