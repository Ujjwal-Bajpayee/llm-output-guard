"""Pydantic integration example for llm-output-guard."""

from typing import List, Optional

from pydantic import BaseModel, Field

from llm_output_guard import Validator


# Define your Pydantic output schema.
class Article(BaseModel):
    title: str
    summary: str = Field(min_length=10)
    tags: List[str] = Field(default_factory=list)
    word_count: Optional[int] = None


# Simulate an LLM.
def fake_llm(prompt: str, **kwargs) -> str:
    return """{
        "title": "The Rise of LLMs",
        "summary": "Large language models are transforming software development.",
        "tags": ["AI", "LLM", "Python"],
        "word_count": 1200
    }"""


# Create the validator with the Pydantic model as the schema.
validator = Validator(
    schema=Article,         # pass the class, not an instance
    llm_callable=fake_llm,
    max_retries=3,
)

result = validator.guard("Write an article about LLMs.")

if result.success:
    article: Article = result.data      # fully typed Pydantic instance
    print(f"Title   : {article.title}")
    print(f"Summary : {article.summary}")
    print(f"Tags    : {', '.join(article.tags)}")
    print(f"Words   : {article.word_count}")
else:
    print("Failed:", result.error_summary)

# You can also raise on failure:
result.raise_for_status()
print("All good!")
