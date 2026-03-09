# llm-output-guard

[![PyPI version](https://img.shields.io/pypi/v/llm-output-guard.svg)](https://pypi.org/project/llm-output-guard/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/Ujjwal-Bajpayee/llm-output-guard/actions/workflows/tests.yml/badge.svg)](https://github.com/Ujjwal-Bajpayee/llm-output-guard/actions/workflows/tests.yml)
[![Coverage](https://img.shields.io/codecov/c/github/Ujjwal-Bajpayee/llm-output-guard)](https://codecov.io/gh/Ujjwal-Bajpayee/llm-output-guard)
[![Downloads](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fpypistats.org%2Fapi%2Fpackages%2Fllm-output-guard%2Frecent&query=%24.data.last_month&label=downloads%2Fmonth&color=brightgreen)](https://pypistats.org/packages/llm-output-guard)

A production-ready Python package that validates LLM outputs against schemas, with automatic JSON extraction and retry logic.

---

## Features

- **Schema-agnostic** — works with [Pydantic v2/v1](https://docs.pydantic.dev/), [JSON Schema](https://json-schema.org/), and plain Python dicts
- **Automatic JSON extraction** — strips markdown fences and prose wrappers from LLM responses
- **Configurable retry** — fixed, exponential, or linear back-off with jitter
- **Zero hard dependencies** — the core works with nothing installed; extras add integrations
- **Integrations** — LangChain, FastAPI, OpenAI SDK
- **CLI** — validate JSON files against schemas from the terminal
- **Fully typed** — `py.typed` marker, complete `mypy --strict` coverage

---

## The Problem It Solves

Getting structured data out of an LLM reliably requires a surprising amount of boilerplate — JSON extraction, schema validation, retry logic with error feedback, and prompt engineering. Here's what that looks like today versus with this package.

<details>
<summary><b>Before — ~100 lines of manual plumbing</b></summary>

```python
import json
import re
import time
from typing import Any, Dict, Optional


class LLMJobValidator:
    def __init__(self, model="gpt-4"):
        self.model = model
        self.max_retries = 3

    def generate_job(self, description: str) -> Optional[Dict]:
        prompt = self._build_prompt(description)

        for attempt in range(self.max_retries):
            response = self._call_llm(prompt)

            data = self._extract_json(response)
            if not data:
                continue

            errors = self._validate_job_data(data)
            if not errors:
                return data

            prompt = self._build_retry_prompt(prompt, errors, response)
            time.sleep(1 * (attempt + 1))

        return None

    def _build_prompt(self, description):
        return f"""
        Create a job posting for: {description}

        Output must be JSON with:
        - title (string): Job title
        - salary (integer): Annual salary in USD
        - skills (array of strings): Required skills
        - is_remote (boolean): Whether remote work is possible

        Example:
        {{
            "title": "Software Engineer",
            "salary": 100000,
            "skills": ["Python", "SQL"],
            "is_remote": true
        }}
        """

    def _extract_json(self, text):
        try:
            return json.loads(text)
        except Exception:
            pass

        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass

        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass

        return None

    def _validate_job_data(self, data):
        errors = {}

        if 'title' not in data:
            errors['title'] = 'Missing title'
        elif not isinstance(data['title'], str):
            errors['title'] = 'Title must be string'

        if 'salary' not in data:
            errors['salary'] = 'Missing salary'
        elif not isinstance(data['salary'], (int, float)):
            errors['salary'] = 'Salary must be number'
        elif data['salary'] <= 0:
            errors['salary'] = 'Salary must be positive'

        if 'skills' not in data:
            errors['skills'] = 'Missing skills'
        elif not isinstance(data['skills'], list):
            errors['skills'] = 'Skills must be array'

        if 'is_remote' not in data:
            errors['is_remote'] = 'Missing is_remote'
        elif not isinstance(data['is_remote'], bool):
            errors['is_remote'] = 'is_remote must be boolean'

        return errors

    def _build_retry_prompt(self, original_prompt, errors, bad_response):
        error_text = "\n".join([f"- {k}: {v}" for k, v in errors.items()])
        return f"""
        {original_prompt}

        Your previous response had these errors:
        {error_text}

        Bad response: {bad_response}

        Please fix these errors and provide valid JSON.
        """

    def _call_llm(self, prompt):
        # your real API call here
        ...
```

</details>

**After — just the schema:**

```python
from pydantic import BaseModel, Field
from llm_output_guard.integrations.openai import GuardedOpenAI


class JobPost(BaseModel):
    title: str = Field(description="Job title")
    salary: int = Field(description="Annual salary in USD", gt=0)
    skills: list[str] = Field(description="Required skills")
    is_remote: bool = Field(description="Whether remote work is possible")


# That's ALL you write. Everything else is handled automatically:
# JSON extraction · schema validation · retry with error feedback · prompt engineering
guard = GuardedOpenAI(schema=JobPost, model="gpt-4o-mini", max_retries=3)

result = guard.guard("Create a software engineer job posting.")
if result.success:
    job: JobPost = result.data          # fully typed Pydantic instance
    print(f"{job.title} — ${job.salary:,} — remote: {job.is_remote}")
```

---

## Installation

```bash
# Core (no dependencies)
pip install llm-output-guard

# With Pydantic v2
pip install "llm-output-guard[pydantic]"

# With JSON Schema validation
pip install "llm-output-guard[jsonschema]"

# With OpenAI integration
pip install "llm-output-guard[openai]"

# With LangChain integration
pip install "llm-output-guard[langchain]"

# Everything
pip install "llm-output-guard[all]"
```

---

## Quick Start

### JSON Schema

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
    return '{"name": "Alice", "age": 30}'

validator = Validator(schema=schema, llm_callable=my_llm, max_retries=2)
result = validator.guard("Who is Alice?")

print(result.success)   # True
print(result.data)      # {'name': 'Alice', 'age': 30}
print(result.attempts)  # 1
```

### Pydantic Model

```python
from pydantic import BaseModel
from llm_output_guard import Validator

class Person(BaseModel):
    name: str
    age: int

validator = Validator(schema=Person, llm_callable=my_llm)
result = validator.guard("Describe Alice.")

person: Person = result.data   # fully typed Pydantic instance
print(person.name)             # Alice
```

### Validate an Existing String

```python
result = Validator(schema=Person).validate_output('{"name": "Bob", "age": 25}')
print(result.success)  # True
```

### Raise on Failure

```python
from llm_output_guard.core.exceptions import MaxRetriesExceededError

validator = Validator(schema=schema, llm_callable=my_llm, raise_on_failure=True)
try:
    result = validator.guard("…")
except MaxRetriesExceededError as e:
    print(f"Failed after {e.attempts} attempts.")
```

---

## Integrations

### OpenAI

```python
from llm_output_guard.integrations.openai import GuardedOpenAI

guard = GuardedOpenAI(schema=Person, model="gpt-4o-mini", max_retries=3)
result = guard.guard("Tell me about Alice.")
```

### LangChain

```python
from langchain_openai import ChatOpenAI
from llm_output_guard.integrations.langchain import GuardedLLM

guarded = GuardedLLM(llm=ChatOpenAI(), schema=Person, max_retries=3)
result = guarded.invoke("Tell me about Alice.")
```

### FastAPI

```python
from fastapi import FastAPI
from llm_output_guard import Validator

app = FastAPI()
validator = Validator(schema=Person, llm_callable=my_llm)

@app.post("/person")
async def get_person(prompt: str):
    result = validator.guard(prompt)
    result.raise_for_status()
    return result.data
```

---

## CLI

```bash
# Validate a JSON file against a JSON Schema file
llm-guard validate output.json schema.json

# Print the JSON Schema of a Pydantic model
llm-guard schema mypackage.models.Person
```

---

## GuardResult

Every `.guard()` or `.validate_output()` call returns a `GuardResult`:

| Attribute     | Type              | Description                              |
|---------------|-------------------|------------------------------------------|
| `success`     | `bool`            | `True` when validation passed            |
| `data`        | `Any`             | Validated output (Pydantic instance or dict) |
| `raw_output`  | `str`             | Raw string from the LLM                  |
| `errors`      | `list[dict]`      | Validation error dicts (empty on success)|
| `attempts`    | `int`             | Number of LLM calls made                 |
| `schema_type` | `str`             | `"pydantic"` / `"json_schema"` / `"dict"` |

---

## Retry Strategies

| Strategy      | Description                              |
|---------------|------------------------------------------|
| `fixed`       | Constant delay between retries           |
| `exponential` | Exponential back-off with optional jitter (default) |
| `linear`      | Linearly increasing delay                |

```python
Validator(schema=schema, llm_callable=llm, retry_strategy="exponential", retry_delay=1.0)
```

---

## Development

```bash
git clone https://github.com/Ujjwal-Bajpayee/llm-output-guard
cd llm-output-guard
pip install -e ".[dev]"
pytest --cov=llm_output_guard
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)

