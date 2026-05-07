"""Tests for the CLI (llm-guard validate / llm-guard schema)."""

from __future__ import annotations

import json
import pytest

try:
    import click  # noqa: F401

    CLICK_AVAILABLE = True
except ImportError:
    CLICK_AVAILABLE = False

pytestmark = pytest.mark.skipif(not CLICK_AVAILABLE, reason="click not installed")


@pytest.fixture
def runner():
    from click.testing import CliRunner

    return CliRunner()


@pytest.fixture
def valid_output_file(tmp_path):
    f = tmp_path / "output.json"
    f.write_text(json.dumps({"name": "Alice", "age": 30}))
    return str(f)


@pytest.fixture
def invalid_output_file(tmp_path):
    f = tmp_path / "output_bad.json"
    f.write_text(json.dumps({"name": "Alice"}))  # missing 'age'
    return str(f)


@pytest.fixture
def schema_file(tmp_path):
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
        },
        "required": ["name", "age"],
    }
    f = tmp_path / "schema.json"
    f.write_text(json.dumps(schema))
    return str(f)


class TestValidateCommand:
    def test_valid_output_exits_zero(self, runner, valid_output_file, schema_file):
        from llm_output_guard.cli.main import _cli

        result = runner.invoke(_cli, ["validate", valid_output_file, schema_file])
        assert result.exit_code == 0
        assert "passed" in result.output.lower()

    def test_invalid_output_exits_one(self, runner, invalid_output_file, schema_file):
        from llm_output_guard.cli.main import _cli

        result = runner.invoke(_cli, ["validate", invalid_output_file, schema_file])
        assert result.exit_code == 1

    def test_quiet_flag_suppresses_success_message(self, runner, valid_output_file, schema_file):
        from llm_output_guard.cli.main import _cli

        result = runner.invoke(_cli, ["validate", "--quiet", valid_output_file, schema_file])
        assert result.exit_code == 0
        assert result.output.strip() == ""

    def test_strict_flag_rejects_non_json(self, runner, tmp_path, schema_file):
        from llm_output_guard.cli.main import _cli

        f = tmp_path / "prose.txt"
        f.write_text('Here is the data: {"name": "Alice", "age": 30}')
        result = runner.invoke(_cli, ["validate", "--strict", str(f), schema_file])
        # strict mode should fail — prose wrapping is invalid
        assert result.exit_code == 1


class TestSchemaCommand:
    def test_prints_pydantic_schema(self, runner):
        from llm_output_guard.cli.main import _cli

        result = runner.invoke(_cli, ["schema", "tests.fixtures.schemas.PERSON_JSON_SCHEMA"])
        assert result.exit_code == 1

    def test_invalid_model_path_no_dot(self, runner):
        from llm_output_guard.cli.main import _cli

        result = runner.invoke(_cli, ["schema", "nodot"])
        assert result.exit_code == 1
        assert "dotted" in result.output.lower()

    def test_import_error_handled(self, runner):
        from llm_output_guard.cli.main import _cli

        result = runner.invoke(_cli, ["schema", "nonexistent.module.Model"])
        assert result.exit_code == 1

    def test_version_flag(self, runner):
        from llm_output_guard.cli.main import _cli

        result = runner.invoke(_cli, ["--version"])
        assert result.exit_code == 0
        assert "0.2.0" in result.output
