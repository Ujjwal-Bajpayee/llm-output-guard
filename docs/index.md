# llm-output-guard

**A production-ready library for validating LLM outputs against schemas.**

`llm-output-guard` bridges the gap between the free-form text that LLMs produce and the structured data your application needs. It handles JSON extraction, schema validation, and automatic retry — so you can focus on building great products.

---

## Highlights

| Feature | Details |
|---------|---------|
| Schema support | Pydantic v2/v1, JSON Schema, plain dict |
| JSON extraction | Strips markdown fences, extracts from prose |
| Retry | Fixed, exponential (with jitter), linear back-off |
| Integrations | OpenAI, LangChain, FastAPI |
| CLI | `llm-guard validate` / `llm-guard schema` |
| Dependencies | Zero hard dependencies for the core |

---

## Getting Started

```bash
pip install "llm-output-guard[pydantic,jsonschema]"
```

```python
from pydantic import BaseModel
from llm_output_guard import Validator

class Person(BaseModel):
    name: str
    age: int

def my_llm(prompt: str) -> str:
    return '{"name": "Alice", "age": 30}'

result = Validator(schema=Person, llm_callable=my_llm).guard("Who is Alice?")
print(result.data)  # Person(name='Alice', age=30)
```

## Navigation

- [Getting Started](getting-started.md)
- [API Reference](api-reference.md)
- Examples
    - [Basic Usage](examples/basic_usage.md)
    - [Pydantic Integration](examples/pydantic_integration.md)
    - [LangChain Integration](examples/langchain_integration.md)
    - [FastAPI Integration](examples/fastapi_integration.md)
