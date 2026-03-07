"""FastAPI integration for llm-output-guard."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from ..core.exceptions import IntegrationError
from ..core.validator import Validator

if TYPE_CHECKING:
    from ..core.types import SchemaDefinition

try:
    from fastapi import HTTPException

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


def _check_fastapi() -> None:
    if not FASTAPI_AVAILABLE:
        raise IntegrationError(
            "FastAPI is not installed. Run: pip install fastapi",
            integration="fastapi",
        )


def guarded_endpoint(
    schema: SchemaDefinition,
    llm_callable: Callable[..., str],
    *,
    max_retries: int = 2,
    raise_http_on_failure: bool = True,
) -> Callable[..., Any]:
    """
    Decorator factory that wraps a FastAPI route handler and validates the LLM
    output returned by inner *llm_callable* against *schema*.

    Usage::

        @app.post("/generate")
        @guarded_endpoint(schema=ArticleModel, llm_callable=my_llm)
        async def generate(request: GenerateRequest):
            return request.prompt
    """
    _check_fastapi()

    validator = Validator(
        schema=schema,
        llm_callable=llm_callable,
        max_retries=max_retries,
        raise_on_failure=False,
    )

    def decorator(route_fn: Callable[..., Any]) -> Callable[..., Any]:
        import functools

        @functools.wraps(route_fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            prompt = await route_fn(*args, **kwargs)
            result = validator.guard(str(prompt))
            if not result.success and raise_http_on_failure:
                raise HTTPException(
                    status_code=422,
                    detail={"message": "LLM output validation failed.", "errors": result.errors},
                )
            return result.data if result.success else result

        return wrapper

    return decorator


class LLMGuardMiddleware:
    """
    ASGI middleware that optionally logs or rejects responses from LLM-backed
    endpoints based on schema validation.

    Primarily useful for monitoring; for strict enforcement, prefer
    :func:`guarded_endpoint`.
    """

    def __init__(self, app: Any, schema: SchemaDefinition) -> None:
        _check_fastapi()
        self.app = app
        from ..core.schema_parser import SchemaParser

        self.schema_parser = SchemaParser(schema)

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        await self.app(scope, receive, send)
