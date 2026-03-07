"""Advanced usage: custom retry strategies, field-level validators, and more."""

from __future__ import annotations

from typing import List

from llm_output_guard import Validator
from llm_output_guard.core.exceptions import MaxRetriesExceededError
from llm_output_guard.retry.strategies import ExponentialBackoffStrategy
from llm_output_guard.utils.validators import is_valid_email, validate_fields


# ---------------------------------------------------------------------------
# 1. Custom retry configuration
# ---------------------------------------------------------------------------

call_count = 0

def flaky_llm(prompt: str, **kwargs) -> str:
    """Simulates a flaky LLM that succeeds on the 3rd call."""
    global call_count
    call_count += 1
    if call_count < 3:
        return "I cannot produce JSON right now."
    return '{"email": "alice@example.com", "username": "alice"}'


schema = {
    "type": "object",
    "properties": {
        "email": {"type": "string"},
        "username": {"type": "string"},
    },
    "required": ["email", "username"],
}

import unittest.mock as mock

with mock.patch("time.sleep"):  # skip actual sleeping
    validator = Validator(
        schema=schema,
        llm_callable=flaky_llm,
        max_retries=5,
        retry_strategy="exponential",
        retry_delay=0.5,
    )
    result = validator.guard("Give me a user JSON.")

print(f"Success: {result.success}, attempts: {result.attempts}")
assert result.success


# ---------------------------------------------------------------------------
# 2. Post-validation field-level checks
# ---------------------------------------------------------------------------

def llm_with_bad_email(prompt: str, **kwargs) -> str:
    return '{"email": "not-an-email", "username": "bob"}'


result2 = Validator(schema=schema, llm_callable=llm_with_bad_email, max_retries=0).guard("test")

if result2.success:
    # Run additional field-level checks
    field_errors = validate_fields(result2.data, {"email": [is_valid_email]})
    if field_errors:
        print("Field validation failed:", field_errors)
    else:
        print("All good!")
else:
    print("Schema validation failed:", result2.error_summary)


# ---------------------------------------------------------------------------
# 3. Using raise_on_failure + exception handling
# ---------------------------------------------------------------------------

def always_bad_llm(prompt: str, **kwargs) -> str:
    return "No JSON here."


try:
    with mock.patch("time.sleep"):
        Validator(
            schema=schema,
            llm_callable=always_bad_llm,
            max_retries=2,
            raise_on_failure=True,
        ).guard("test")
except MaxRetriesExceededError as exc:
    print(f"Caught MaxRetriesExceededError after {exc.attempts} attempt(s).")
