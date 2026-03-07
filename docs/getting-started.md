# Getting Started

## Installation

`llm-output-guard` has no hard runtime dependencies. Install only what you need:

```bash
# Core only
pip install llm-output-guard

# Core + Pydantic v2
pip install "llm-output-guard[pydantic]"

# Core + JSON Schema validation
pip install "llm-output-guard[jsonschema]"

# Core + OpenAI integration
pip install "llm-output-guard[openai]"

# Core + LangChain integration
pip install "llm-output-guard[langchain]"

# Core + FastAPI integration
pip install "llm-output-guard[fastapi]"

# Everything
pip install "llm-output-guard[all]"
```

---

## Core Concepts

### Validator

`Validator` is the primary entry-point. You provide:

1. A **schema** — Pydantic model class, JSON Schema dict, or plain dict.
2. An **LLM callable** — any `(prompt: str, **kwargs) -> str` function.

```python
from llm_output_guard import Validator

validator = Validator(
    schema=my_schema,
    llm_callable=my_llm,
    max_retries=2,              # default: 2
    retry_strategy="exponential",  # "fixed" | "exponential" | "linear"
    retry_delay=1.0,            # base delay in seconds
    raise_on_failure=False,     # raise MaxRetriesExceededError on failure?
    strict_json=False,          # require the full response to be valid JSON?
    system_prompt=None,         # optional system-level instructions
)
```

### guard()

```python
result = validator.guard("Your prompt here.")
```

- Augments the prompt with schema instructions.
- Calls the LLM.
- Extracts and parses JSON from the response.
- Validates against the schema.
- Retries on failure up to `max_retries` times.

### validate_output()

Validate an existing string without calling the LLM:

```python
result = Validator(schema=my_schema).validate_output('{"name": "Alice", "age": 30}')
```

### GuardResult

Both methods return a `GuardResult`:

```python
result.success       # bool
result.data          # validated object (Pydantic instance or dict), or None
result.raw_output    # raw LLM string
result.errors        # list of validation error dicts
result.attempts      # int — number of LLM calls made
result.schema_type   # "pydantic" | "json_schema" | "dict"

result.raise_for_status()   # raises ValidationError if not success
result.error_summary        # formatted string of all errors
```

---

## Schema Types

### Pydantic Model

```python
from pydantic import BaseModel
from llm_output_guard import Validator

class Person(BaseModel):
    name: str
    age: int

result = Validator(schema=Person, llm_callable=llm).guard("Who is Alice?")
person: Person = result.data   # fully typed
```

### JSON Schema Dict

```python
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age":  {"type": "integer"},
    },
    "required": ["name", "age"],
}

result = Validator(schema=schema, llm_callable=llm).guard("Who is Alice?")
assert result.data["name"] == "Alice"
```

### Plain Dict Schema

```python
schema = {"name": str, "age": int}   # type-checks only

# Use Ellipsis to mark a field as required (any type)
strict_schema = {"name": ..., "score": float}
```

---

## Retry Strategies

| Strategy | Delay formula |
|----------|---------------|
| `fixed` | `base_delay` |
| `exponential` | `base_delay * 2^(attempt-1)`, with optional jitter |
| `linear` | `base_delay * attempt` |

```python
Validator(schema=schema, llm_callable=llm, retry_strategy="exponential", retry_delay=0.5)
```

---

## CLI

```bash
# Validate output.json against schema.json
llm-guard validate output.json schema.json

# Print JSON Schema for a Pydantic model
llm-guard schema mypackage.models.Person --indent 4
```
