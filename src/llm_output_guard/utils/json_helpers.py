"""JSON parsing and extraction utilities."""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from ..core.exceptions import JSONParseError


def parse_json_safely(text: str) -> Any:
    """
    Parse *text* as JSON, raising :exc:`JSONParseError` on failure.

    This is a thin wrapper that produces a more descriptive error message than
    the built-in ``json.loads``.
    """
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError as exc:
        snippet = text[:120].replace("\n", " ")
        raise JSONParseError(
            f"Cannot parse JSON: {exc.msg} (at line {exc.lineno}, col {exc.colno}).",
            raw_output=snippet,
        ) from exc


def extract_json(text: str) -> Any:
    """
    Extract and parse the *first* JSON object or array from *text*.

    Handles common LLM quirks:
    - Markdown code fences (```json … ``` or ``` … ```)
    - Leading/trailing prose around a JSON block
    - Single-quoted JSON (best-effort repair)

    Raises :exc:`JSONParseError` if no valid JSON can be found.
    """
    stripped = text.strip()

    # 1. Try parsing the whole response first (fastest path).
    try:
        return parse_json_safely(stripped)
    except JSONParseError:
        pass

    # 2. Extract from markdown code fence.
    fence_match = re.search(
        r"```(?:json)?\s*\n?([\s\S]*?)\n?```", stripped, re.IGNORECASE
    )
    if fence_match:
        candidate = fence_match.group(1).strip()
        try:
            return parse_json_safely(candidate)
        except JSONParseError:
            pass

    # 3. Scan for the first { … } or [ … ] block.
    for start_char, end_char in (("{", "}"), ("[", "]")):
        start_idx = stripped.find(start_char)
        if start_idx == -1:
            continue
        # Walk from the end to find the matching closer.
        end_idx = stripped.rfind(end_char)
        if end_idx <= start_idx:
            continue
        candidate = stripped[start_idx : end_idx + 1]
        try:
            return parse_json_safely(candidate)
        except JSONParseError:
            pass

    # 4. Best-effort: replace single quotes with double quotes.
    repaired = _repair_single_quotes(stripped)
    if repaired != stripped:
        try:
            return parse_json_safely(repaired)
        except JSONParseError:
            pass

    raise JSONParseError(
        "Could not extract valid JSON from the LLM response.",
        raw_output=text[:200],
    )


def _repair_single_quotes(text: str) -> str:
    """Very naïve single-quote → double-quote substitution."""
    # Only attempt when the string looks JSON-like.
    if "{" not in text and "[" not in text:
        return text
    return text.replace("'", '"')


def to_json_string(obj: Any, indent: int = 2) -> str:
    """Serialise *obj* to a pretty-printed JSON string."""
    try:
        return json.dumps(obj, indent=indent, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise JSONParseError(f"Cannot serialise object to JSON: {exc}") from exc
