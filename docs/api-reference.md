# API Reference

## `llm_output_guard.Validator`

The main class for guarding LLM outputs.

```python
class Validator(
    schema: SchemaDefinition,
    llm_callable: Optional[LLMCallable] = None,
    *,
    max_retries: int = 2,
    retry_strategy: str = "exponential",
    retry_delay: float = 1.0,
    raise_on_failure: bool = False,
    strict_json: bool = False,
    system_prompt: Optional[str] = None,
)
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `schema` | Pydantic class / dict | — | Schema to validate against |
| `llm_callable` | `(str, **kwargs) -> str` | `None` | Callable that calls the LLM |
| `max_retries` | `int` | `2` | Extra retry attempts on failure |
| `retry_strategy` | `str` | `"exponential"` | `"fixed"` / `"exponential"` / `"linear"` |
| `retry_delay` | `float` | `1.0` | Base delay (seconds) between retries |
| `raise_on_failure` | `bool` | `False` | Raise `MaxRetriesExceededError` if all retries fail |
| `strict_json` | `bool` | `False` | Require entire response to be valid JSON |
| `system_prompt` | `str` | `None` | System-level instructions prepended to every prompt |

### Methods

#### `guard(prompt, **llm_kwargs) -> GuardResult`

Call the LLM and validate. Retries automatically on failure.

#### `validate_output(raw_output) -> GuardResult`

Validate an existing string. No LLM call is made.

---

## `llm_output_guard.GuardResult`

```python
@dataclass
class GuardResult:
    success: bool
    data: Optional[Any]
    raw_output: str
    errors: List[Dict[str, Any]]
    attempts: int
    schema_type: str
```

### Methods

#### `raise_for_status() -> GuardResult`

Raises `ValidationError` if `success` is `False`. Returns `self` otherwise.

#### `error_summary -> str` (property)

Human-readable summary of all validation errors.

---

## `llm_output_guard.SchemaParser`

Low-level schema detection and validation.

```python
parser = SchemaParser(schema)
parser.schema_type        # SchemaType enum
parser.json_schema        # JSON Schema dict representation
parser.describe()         # human-readable description string
result, errors = parser.validate(data)  # validate a dict/list
```

---

## Exceptions

| Exception | Description |
|-----------|-------------|
| `LLMOutputGuardError` | Base class for all errors |
| `ValidationError` | Schema validation failed |
| `SchemaParseError` | Schema cannot be parsed |
| `JSONParseError` | LLM output cannot be parsed as JSON |
| `MaxRetriesExceededError` | All retry attempts exhausted |
| `IntegrationError` | Third-party integration error |

---

## Integrations

### `llm_output_guard.integrations.openai.GuardedOpenAI`

```python
GuardedOpenAI(
    schema, *, model="gpt-4o-mini", api_key=None, temperature=0.0,
    max_tokens=None, max_retries=2, retry_strategy="exponential",
    raise_on_failure=False, system_prompt=None, extra_openai_kwargs=None
)
```

### `llm_output_guard.integrations.langchain.GuardedLLM`

```python
GuardedLLM(llm, schema, *, max_retries=2, retry_strategy="exponential", raise_on_failure=False)
result = guarded.invoke(prompt)
```

### `llm_output_guard.integrations.langchain.GuardOutputParser`

```python
parser = GuardOutputParser(schema)
data = parser.parse(text)            # raises ValidationError on failure
instructions = parser.get_format_instructions()
```

### `llm_output_guard.integrations.fastapi.guarded_endpoint`

```python
@app.post("/route")
@guarded_endpoint(schema=MyModel, llm_callable=my_llm, max_retries=2)
async def route(request: Request):
    return prompt_string
```

---

## Utilities

### `llm_output_guard.utils.json_helpers`

| Function | Description |
|----------|-------------|
| `extract_json(text)` | Extract JSON from prose/markdown |
| `parse_json_safely(text)` | Parse JSON, raise `JSONParseError` on failure |
| `to_json_string(obj)` | Serialise object to indented JSON |

### `llm_output_guard.utils.validators`

| Function | Description |
|----------|-------------|
| `is_non_empty_string(v)` | Non-empty string check |
| `is_positive_number(v)` | Positive int/float check |
| `is_valid_email(v)` | Basic email format check |
| `is_valid_url(v)` | Basic HTTP/HTTPS URL check |
| `is_non_empty_list(v)` | Non-empty list check |
| `validate_fields(data, rules)` | Apply validators to specific fields |
