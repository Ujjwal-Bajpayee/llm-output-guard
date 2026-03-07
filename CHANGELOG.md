# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Nothing yet.

---

## [0.1.0] — 2024-03-07

### Added
- `Validator` class with `guard()` and `validate_output()` methods.
- `GuardResult` dataclass with `raise_for_status()`, `error_summary`, and metadata fields.
- `SchemaParser` supporting Pydantic v2/v1, JSON Schema (via `jsonschema`), and plain dict schemas.
- Automatic JSON extraction from prose and markdown code fences.
- `RetryManager` with `fixed`, `exponential`, and `linear` back-off strategies.
- OpenAI integration (`GuardedOpenAI`).
- LangChain integration (`GuardedLLM`, `GuardOutputParser`).
- FastAPI integration (`guarded_endpoint`, `LLMGuardMiddleware`).
- CLI commands `llm-guard validate` and `llm-guard schema`.
- Field-level validators (`is_valid_email`, `is_valid_url`, etc.).
- Comprehensive test suite (unit + integration).
- Zero hard dependencies for the core package; all integrations are optional extras.

[Unreleased]: https://github.com/Ujjwal-Bajpayee/llm-output-guard/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Ujjwal-Bajpayee/llm-output-guard/releases/tag/v0.1.0


