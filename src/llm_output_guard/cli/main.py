"""CLI for llm-output-guard — validate a raw JSON file against a JSON Schema."""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import click

    CLICK_AVAILABLE = True
except ImportError:
    CLICK_AVAILABLE = False


def _no_click() -> None:
    print(
        "The llm-output-guard CLI requires 'click'. "
        "Install it with: pip install llm-output-guard[cli]",
        file=sys.stderr,
    )
    sys.exit(1)


def main() -> None:
    """Entry-point registered in pyproject.toml."""
    if not CLICK_AVAILABLE:
        _no_click()
    _cli()


if CLICK_AVAILABLE:
    import click

    @click.group()
    @click.version_option(package_name="llm-output-guard")
    def _cli() -> None:
        """llm-output-guard — validate LLM outputs against schemas."""

    @_cli.command("validate")
    @click.argument("output_file", type=click.Path(exists=True))
    @click.argument("schema_file", type=click.Path(exists=True))
    @click.option("--strict", is_flag=True, help="Strict JSON mode (no extraction).")
    @click.option("--quiet", "-q", is_flag=True, help="Suppress success messages.")
    def validate_cmd(output_file: str, schema_file: str, strict: bool, quiet: bool) -> None:
        """Validate OUTPUT_FILE (JSON) against SCHEMA_FILE (JSON Schema)."""
        from llm_output_guard import Validator

        output_path = Path(output_file)
        schema_path = Path(schema_file)

        raw = output_path.read_text(encoding="utf-8")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        validator = Validator(schema=schema, strict_json=strict)
        result = validator.validate_output(raw)

        if result.success:
            if not quiet:
                click.secho("✓ Validation passed.", fg="green")
            sys.exit(0)
        else:
            click.secho("✗ Validation failed:", fg="red", err=True)
            click.echo(result.error_summary, err=True)
            sys.exit(1)

    @_cli.command("schema")
    @click.argument("model_path", type=str)
    @click.option("--indent", default=2, show_default=True, help="JSON indent level.")
    def schema_cmd(model_path: str, indent: int) -> None:
        """
        Print the JSON Schema for a Python Pydantic model.

        MODEL_PATH is a dotted import path, e.g. mypackage.models.MyModel
        """
        import importlib

        parts = model_path.rsplit(".", 1)
        if len(parts) != 2:
            click.echo("Error: MODEL_PATH must be a dotted import path.", err=True)
            sys.exit(1)

        module_path, class_name = parts
        try:
            module = importlib.import_module(module_path)
            model_cls = getattr(module, class_name)
        except (ImportError, AttributeError) as exc:
            click.echo(f"Error importing {model_path!r}: {exc}", err=True)
            sys.exit(1)

        from llm_output_guard.core.schema_parser import pydantic_schema_to_json

        schema = pydantic_schema_to_json(model_cls)
        click.echo(json.dumps(schema, indent=indent))

else:

    def _cli() -> None:  # type: ignore[misc]
        _no_click()
