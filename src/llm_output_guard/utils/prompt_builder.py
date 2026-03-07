"""Utilities for building prompts that instruct the LLM to return structured output."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


_DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful assistant that always responds with valid JSON. "
    "Do not include any text outside the JSON object."
)

_SCHEMA_INSTRUCTION_TEMPLATE = """
You MUST respond with a single JSON object that conforms exactly to the following schema:

{schema}

Return ONLY valid JSON. Do not include any explanation, markdown fences, or extra text.
"""

_ERROR_CORRECTION_TEMPLATE = """
Your previous response did not conform to the required schema.

Validation errors:
{errors}

Please provide a corrected JSON response that conforms to:

{schema}

Return ONLY valid JSON.
"""


def build_validation_prompt(
    prompt: str,
    schema_description: str,
    system_prompt: Optional[str] = None,
    previous_errors: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Construct the full prompt sent to the LLM.

    When *previous_errors* are provided the prompt includes corrective
    instructions that show the LLM what went wrong.
    """
    sys = system_prompt or _DEFAULT_SYSTEM_PROMPT
    schema_block = _SCHEMA_INSTRUCTION_TEMPLATE.format(schema=schema_description)

    if previous_errors:
        error_lines = _format_errors_for_prompt(previous_errors)
        correction_block = _ERROR_CORRECTION_TEMPLATE.format(
            errors=error_lines,
            schema=schema_description,
        )
        parts = [sys.strip(), correction_block.strip(), prompt.strip()]
    else:
        parts = [sys.strip(), schema_block.strip(), prompt.strip()]

    return "\n\n".join(parts)


def _format_errors_for_prompt(errors: List[Dict[str, Any]]) -> str:
    lines = []
    for err in errors:
        loc = " -> ".join(str(x) for x in err.get("loc", []))
        msg = err.get("msg", "Unknown error")
        lines.append(f"- [{loc}]: {msg}" if loc else f"- {msg}")
    return "\n".join(lines) if lines else "Unknown validation errors."


def build_system_prompt(schema_description: str) -> str:
    """Return a system-level prompt that instructs the model to return JSON."""
    return (
        "You are a helpful assistant that always responds with valid JSON. "
        "Do not include any text outside the JSON object.\n\n"
        f"Always return a JSON object matching this schema:\n{schema_description}"
    )
