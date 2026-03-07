# Basic Usage

This page walks through the most common patterns for using `llm-output-guard`.

## Installation

```bash
pip install "llm-output-guard[jsonschema]"
```

## 1. Validate Using a JSON Schema

```python
from llm_output_guard import Validator

schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age":  {"type": "integer"},
    },
    "required": ["name", "age"],
}

def my_llm(prompt: str) -> str:
    # Replace with your real LLM call
    return '{"name": "Alice", "age": 30}'

validator = Validator(schema=schema, llm_callable=my_llm)
result = validator.guard("Who is Alice?")

print(result.success)   # True
print(result.data)      # {'name': 'Alice', 'age': 30}
```

## 2. Validate an Existing String

No LLM call is made — useful for testing or post-processing:

```python
result = Validator(schema=schema).validate_output('{"name": "Alice", "age": 30}')
```

## 3. Handle Failures Gracefully

```python
validator = Validator(schema=schema, llm_callable=my_llm, max_retries=3)
result = validator.guard("Describe Bob.")

if result.success:
    process(result.data)
else:
    print(result.error_summary)
```

## 4. Raise on Failure

```python
from llm_output_guard.core.exceptions import MaxRetriesExceededError

validator = Validator(schema=schema, llm_callable=my_llm, raise_on_failure=True)
try:
    result = validator.guard("Describe Bob.")
except MaxRetriesExceededError as e:
    print(f"Failed after {e.attempts} attempt(s).")
```

## 5. Using `raise_for_status()`

```python
result = validator.guard("test").raise_for_status()
# Proceeds only if validation passed; otherwise raises ValidationError
```
