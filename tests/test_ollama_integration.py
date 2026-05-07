"""Tests for Ollama integration."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from llm_output_guard.core.exceptions import IntegrationError


class TestOllamaIntegration:
    def test_import_without_requests(self):
        """GuardedOllama raises IntegrationError when requests is absent."""
        import llm_output_guard.integrations.ollama as ollama_mod

        original = ollama_mod.REQUESTS_AVAILABLE
        ollama_mod.REQUESTS_AVAILABLE = False
        try:
            with pytest.raises(IntegrationError, match="requests"):
                ollama_mod.GuardedOllama(schema={"type": "object"}, model="mistral")
        finally:
            ollama_mod.REQUESTS_AVAILABLE = original

    def test_missing_model_raises_error(self):
        """GuardedOllama raises IntegrationError when model is not provided."""
        from llm_output_guard.integrations.ollama import REQUESTS_AVAILABLE, GuardedOllama

        if not REQUESTS_AVAILABLE:
            pytest.skip("requests not installed")

        with pytest.raises(IntegrationError, match="Model name must be provided"):
            GuardedOllama(schema={"type": "object"})

    def test_model_from_env_variable(self):
        """GuardedOllama uses OLLAMA_MODEL environment variable if provided."""
        from llm_output_guard.integrations.ollama import REQUESTS_AVAILABLE, GuardedOllama

        if not REQUESTS_AVAILABLE:
            pytest.skip("requests not installed")

        with patch.dict("os.environ", {"OLLAMA_MODEL": "llama2"}), patch("requests.post"):
            guard = GuardedOllama(schema={"type": "object"})
            assert guard.model == "llama2"

    def test_base_url_from_env_variable(self):
        """GuardedOllama uses OLLAMA_BASE_URL environment variable if provided."""
        from llm_output_guard.integrations.ollama import REQUESTS_AVAILABLE, GuardedOllama

        if not REQUESTS_AVAILABLE:
            pytest.skip("requests not installed")

        with (
            patch.dict(
                "os.environ", {"OLLAMA_BASE_URL": "http://custom:8080", "OLLAMA_MODEL": "mistral"}
            ),
            patch("requests.post"),
        ):
            guard = GuardedOllama(schema={"type": "object"})
            assert guard.base_url == "http://custom:8080"

    def test_default_base_url(self):
        """GuardedOllama uses default base URL when not provided."""
        from llm_output_guard.integrations.ollama import REQUESTS_AVAILABLE, GuardedOllama

        if not REQUESTS_AVAILABLE:
            pytest.skip("requests not installed")

        with (
            patch.dict("os.environ", {"OLLAMA_MODEL": "mistral"}, clear=True),
            patch("requests.post"),
        ):
            guard = GuardedOllama(schema={"type": "object"})
            assert guard.base_url == "http://localhost:11434"

    def test_guarded_ollama_successful_call(self):
        """GuardedOllama.guard makes successful API call and validates output."""
        from llm_output_guard.integrations.ollama import REQUESTS_AVAILABLE, GuardedOllama

        if not REQUESTS_AVAILABLE:
            pytest.skip("requests not installed")

        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            "required": ["name", "age"],
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {"response": '{"name": "Alice", "age": 30}'}

        with patch("requests.post", return_value=mock_response), patch("time.sleep"):
            guard = GuardedOllama(schema=schema, model="mistral", max_retries=0)
            result = guard.guard("Extract user info")

        assert result.success is True
        assert result.data["name"] == "Alice"
        assert result.data["age"] == 30

    def test_guarded_ollama_connection_error(self):
        """GuardedOllama raises IntegrationError on connection failure."""
        from llm_output_guard.integrations.ollama import REQUESTS_AVAILABLE, GuardedOllama

        if not REQUESTS_AVAILABLE:
            pytest.skip("requests not installed")

        schema = {"type": "object", "properties": {"name": {"type": "string"}}}

        with (
            patch("requests.post", side_effect=__import__("requests").exceptions.ConnectionError()),
            pytest.raises(IntegrationError, match="Failed to connect"),
        ):
            guard = GuardedOllama(
                schema=schema, model="mistral", raise_on_failure=True, max_retries=0
            )
            guard.guard("test")

    def test_guarded_ollama_timeout_error(self):
        """GuardedOllama raises IntegrationError on timeout."""
        from llm_output_guard.integrations.ollama import REQUESTS_AVAILABLE, GuardedOllama

        if not REQUESTS_AVAILABLE:
            pytest.skip("requests not installed")

        schema = {"type": "object", "properties": {"name": {"type": "string"}}}

        with (
            patch("requests.post", side_effect=__import__("requests").exceptions.Timeout()),
            pytest.raises(IntegrationError, match="timed out"),
        ):
            guard = GuardedOllama(
                schema=schema, model="mistral", raise_on_failure=True, max_retries=0
            )
            guard.guard("test")

    def test_guarded_ollama_http_error(self):
        """GuardedOllama raises IntegrationError on HTTP error."""
        from llm_output_guard.integrations.ollama import REQUESTS_AVAILABLE, GuardedOllama

        if not REQUESTS_AVAILABLE:
            pytest.skip("requests not installed")

        schema = {"type": "object", "properties": {"name": {"type": "string"}}}

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = __import__("requests").exceptions.HTTPError(
            response=mock_response
        )

        with (
            patch("requests.post", return_value=mock_response),
            pytest.raises(IntegrationError, match="API error"),
        ):
            guard = GuardedOllama(
                schema=schema, model="mistral", raise_on_failure=True, max_retries=0
            )
            guard.guard("test")

    def test_guarded_ollama_unexpected_response_format(self):
        """GuardedOllama raises IntegrationError on unexpected response format."""
        from llm_output_guard.integrations.ollama import REQUESTS_AVAILABLE, GuardedOllama

        if not REQUESTS_AVAILABLE:
            pytest.skip("requests not installed")

        schema = {"type": "object", "properties": {"name": {"type": "string"}}}

        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "something went wrong"}

        with (
            patch("requests.post", return_value=mock_response),
            pytest.raises(IntegrationError, match="Unexpected Ollama response"),
        ):
            guard = GuardedOllama(
                schema=schema, model="mistral", raise_on_failure=True, max_retries=0
            )
            guard.guard("test")

    def test_validate_output_without_api_call(self):
        """validate_output works without making an API call."""
        from llm_output_guard.integrations.ollama import REQUESTS_AVAILABLE, GuardedOllama

        if not REQUESTS_AVAILABLE:
            pytest.skip("requests not installed")

        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        with patch("requests.post"):
            guard = GuardedOllama(schema=schema, model="mistral")
            result = guard.validate_output('{"name": "Alice"}')

        assert result.success is True
        assert result.data["name"] == "Alice"

    def test_ollama_parameters_passed_correctly(self):
        """GuardedOllama passes temperature and max_tokens correctly."""
        from llm_output_guard.integrations.ollama import REQUESTS_AVAILABLE, GuardedOllama

        if not REQUESTS_AVAILABLE:
            pytest.skip("requests not installed")

        schema = {"type": "object", "properties": {"name": {"type": "string"}}}

        mock_response = MagicMock()
        mock_response.json.return_value = {"response": '{"name": "Alice"}'}

        with patch("requests.post", return_value=mock_response) as mock_post, patch("time.sleep"):
            guard = GuardedOllama(
                schema=schema,
                model="mistral",
                temperature=0.7,
                max_tokens=100,
                max_retries=0,
            )
            guard.guard("test")

        # Verify the API was called with correct parameters
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["temperature"] == 0.7
        assert call_kwargs["json"]["num_predict"] == 100
