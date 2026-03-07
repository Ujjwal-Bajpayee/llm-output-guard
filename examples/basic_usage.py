"""Basic usage example for llm-output-guard."""

from llm_output_guard import Validator


# A simple in-process "LLM" for demonstration purposes.
def fake_llm(prompt: str, **kwargs) -> str:
    """Simulate an LLM response — replace with a real call in production."""
    return '{"name": "Alice", "age": 30, "city": "Wonderland"}'


# 1. Define a schema as a plain JSON Schema dict.
person_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "city": {"type": "string"},
    },
    "required": ["name", "age"],
}

# 2. Create a Validator.
validator = Validator(
    schema=person_schema,
    llm_callable=fake_llm,
    max_retries=2,              # retry up to 2 additional times on failure
    retry_strategy="exponential",
    raise_on_failure=False,     # return a GuardResult even on failure
)

# 3. Guard a prompt.
result = validator.guard("Tell me about Alice.")

if result.success:
    print("Validated data:", result.data)
    print("Attempts needed:", result.attempts)
else:
    print("Validation failed:", result.error_summary)

# 4. Validate an existing string (no LLM call).
raw = '{"name": "Bob", "age": 25}'
result2 = Validator(schema=person_schema).validate_output(raw)
print("Direct validation:", result2.success)
