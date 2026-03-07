# Pydantic Integration

`llm-output-guard` has first-class support for Pydantic v2 (and v1).

## Installation

```bash
pip install "llm-output-guard[pydantic]"
```

## Define Your Output Schema

```python
from typing import List, Optional
from pydantic import BaseModel, Field

class Article(BaseModel):
    title: str
    summary: str = Field(min_length=10)
    tags: List[str] = Field(default_factory=list)
    word_count: Optional[int] = None
```

## Use It with Validator

```python
from llm_output_guard import Validator

def my_llm(prompt: str) -> str:
    return """{
        "title": "The Rise of LLMs",
        "summary": "Large language models are transforming software.",
        "tags": ["AI", "ML"],
        "word_count": 850
    }"""

validator = Validator(schema=Article, llm_callable=my_llm)
result = validator.guard("Write an article about LLMs.")

article: Article = result.data   # fully typed instance
print(article.title)
print(article.tags)
```

## Nested Models

Nested Pydantic models work out of the box:

```python
class Address(BaseModel):
    street: str
    city: str

class Person(BaseModel):
    name: str
    age: int
    address: Address

validator = Validator(schema=Person, llm_callable=my_llm)
result = validator.guard("Describe Alice.")
print(result.data.address.city)
```

## Getting the JSON Schema

```python
from llm_output_guard import SchemaParser

parser = SchemaParser(Article)
print(parser.json_schema)    # dict
print(parser.describe())     # formatted JSON string
```
