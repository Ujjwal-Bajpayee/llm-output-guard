"""FastAPI integration example for llm-output-guard.

Prerequisites:
    pip install llm-output-guard fastapi uvicorn

Run with:
    uvicorn examples.fastapi_example:app --reload
"""

from typing import List

from pydantic import BaseModel

try:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


class SummaryRequest(BaseModel):
    text: str
    max_bullets: int = 5


class SummaryResponse(BaseModel):
    bullets: List[str]
    topic: str


# A fake LLM — replace with a real one.
def fake_llm(prompt: str, **kwargs) -> str:
    return '{"bullets": ["Point 1", "Point 2", "Point 3"], "topic": "AI Safety"}'


if FASTAPI_AVAILABLE:
    from llm_output_guard import Validator
    from llm_output_guard.integrations.fastapi import guarded_endpoint

    app = FastAPI(title="LLM Output Guard — FastAPI Demo")

    # Approach: use Validator directly inside the route
    _validator = Validator(
        schema=SummaryResponse,
        llm_callable=fake_llm,
        max_retries=2,
        raise_on_failure=True,
    )

    @app.post("/summarise", response_model=SummaryResponse)
    async def summarise(request: SummaryRequest):
        prompt = (
            f"Summarise the following text in {request.max_bullets} bullet points "
            f"as JSON:\n\n{request.text}"
        )
        result = _validator.guard(prompt)
        return result.data

    @app.get("/health")
    async def health():
        return {"status": "ok"}

else:
    print("FastAPI not installed. Run: pip install fastapi uvicorn")
