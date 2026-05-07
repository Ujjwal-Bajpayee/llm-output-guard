"""Additional field-level validators used internally and exposed for users."""

from __future__ import annotations

import re
from typing import Any


def is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and len(value.strip()) > 0


def is_positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and value > 0


def is_valid_email(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, value))


def is_valid_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return bool(re.match(pattern, value, re.IGNORECASE))


def is_non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and len(value) > 0


def validate_fields(
    data: dict[str, Any],
    rules: dict[str, list[Any]],
) -> list[dict[str, Any]]:
    """
    Apply a set of validator functions to specific fields of *data*.

    *rules* maps field names to lists of callables::

        errors = validate_fields(
            data,
            {
                "email": [is_valid_email],
                "age": [is_positive_number],
            },
        )

    Returns a list of error dicts (empty on success).
    """
    errors: list[dict[str, Any]] = []
    for field_name, validators in rules.items():
        value = data.get(field_name)
        for validator_fn in validators:
            if not validator_fn(value):
                errors.append(
                    {
                        "loc": [field_name],
                        "msg": f"Value {value!r} failed validator {validator_fn.__name__!r}.",
                        "type": "value_error",
                    }
                )
    return errors
