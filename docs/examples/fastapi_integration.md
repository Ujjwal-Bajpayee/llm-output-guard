# FastAPI Integration

`llm-output-guard` integrates with FastAPI to validate LLM outputs inside route handlers.

## Installation

```bash
pip install "llm-output-guard[fastapi,pydantic]" uvicorn
```

## Option A: Direct Validator in a Route

The simplest approach — use `Validator` directly inside your request handler:

```python
from fastapi import FastAPI
from pydantic import BaseModel
from llm_output_guard import Validator

class SummaryRequest(BaseModel):
    text: str

class SummaryResponse(BaseModel):
    bullets: list[str]
    topic: str

def my_llm(prompt: str) -> str:
    # replace with a real LLM call
    return '{"bullets": ["Point 1", "Point 2"], "topic": "AI"}'

app = FastAPI()
validator = Validator(schema=SummaryResponse, llm_callable=my_llm, max_retries=2)

@app.post("/summarise", response_model=SummaryResponse)
async def summarise(request: SummaryRequest):
    result = validator.guard(f"Summarise: {request.text}")
    result.raise_for_status()   # → 500 on failure; handle explicitly for 422
    return result.data
```

## Option B: `guarded_endpoint` Decorator

```python
from llm_output_guard.integrations.fastapi import guarded_endpoint

@app.post("/summarise")
@guarded_endpoint(
    schema=SummaryResponse,
    llm_callable=my_llm,
    max_retries=3,
    raise_http_on_failure=True,    # returns HTTP 422 on failure
)
async def summarise(request: SummaryRequest):
    # return the prompt string — the decorator handles the LLM call
    return f"Summarise: {request.text}"
```

## Running the Server

```bash
uvicorn myapp:app --reload
```

Then call the endpoint:

```bash
curl -X POST http://localhost:8000/summarise \
     -H "Content-Type: application/json" \
     -d '{"text": "LLMs are increasingly used in production..."}'
```
