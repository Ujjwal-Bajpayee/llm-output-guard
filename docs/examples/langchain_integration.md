# LangChain Integration

`llm-output-guard` provides two LangChain integration points:

1. **`GuardedLLM`** — wraps any LangChain LLM/chat model
2. **`GuardOutputParser`** — LCEL-compatible output parser

## Installation

```bash
pip install "llm-output-guard[langchain,pydantic]" langchain-openai
```

## Option A: GuardedLLM

```python
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from llm_output_guard.integrations.langchain import GuardedLLM

class MovieReview(BaseModel):
    title: str
    rating: float
    verdict: str

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
guarded = GuardedLLM(llm=llm, schema=MovieReview, max_retries=3)

result = guarded.invoke("Review the movie Dune: Part Two.")
review: MovieReview = result.data
print(f"{review.title}: {review.rating}/10 — {review.verdict}")
```

## Option B: GuardOutputParser in an LCEL Chain

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from llm_output_guard.integrations.langchain import GuardOutputParser

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a film critic. Respond in JSON only."),
    ("human", "{question}"),
])
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
parser = GuardOutputParser(schema=MovieReview)

chain = prompt | llm | parser
review = chain.invoke({"question": "Review Oppenheimer (2023)."})
print(review)
```

The parser raises `ValidationError` (which LangChain will surface) if the output doesn't conform to the schema.

## Format Instructions

```python
parser = GuardOutputParser(schema=MovieReview)
print(parser.get_format_instructions())
# → "Return a JSON object matching this schema: ..."
```
