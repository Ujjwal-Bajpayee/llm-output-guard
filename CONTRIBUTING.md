# Contributing to llm-output-guard

Thank you for your interest in contributing! This document describes the process for reporting bugs, proposing features, and submitting code.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How to Report a Bug](#how-to-report-a-bug)
3. [How to Propose a Feature](#how-to-propose-a-feature)
4. [Development Setup](#development-setup)
5. [Running Tests](#running-tests)
6. [Code Style](#code-style)
7. [Submitting a Pull Request](#submitting-a-pull-request)
8. [Release Process](#release-process)

---

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

---

## How to Report a Bug

1. Search [existing issues](https://github.com/Ujjwal-Bajpayee/llm-output-guard/issues) to check the bug hasn't been reported.
2. Open a new issue using the **Bug Report** template.
3. Include:
   - Python version and OS
   - `llm-output-guard` version (`pip show llm-output-guard`)
   - Minimal reproducible example
   - Full traceback

---

## How to Propose a Feature

1. Check [existing issues](https://github.com/Ujjwal-Bajpayee/llm-output-guard/issues) and open discussions.
2. Open a new issue using the **Feature Request** template.
3. Describe the problem it solves and your proposed API surface.

---

## Development Setup

```bash
# Clone the repository
git clone https://github.com/Ujjwal-Bajpayee/llm-output-guard
cd llm-output-guard

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install in editable mode with all dev extras
pip install -e ".[dev,all]"

# Install pre-commit hooks
pre-commit install
```

---

## Running Tests

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=llm_output_guard --cov-report=term-missing

# Run a specific test file
pytest tests/test_validator.py -v

# Run only fast tests (no integration)
pytest -m "not integration"
```

---

## Code Style

This project uses **Ruff** for linting and formatting.

```bash
# Check
ruff check src tests

# Auto-fix
ruff check --fix src tests

# Format
ruff format src tests
```

Type checking with **mypy**:

```bash
mypy src/llm_output_guard
```

Pre-commit runs both automatically on each commit when hooks are installed.

---

## Submitting a Pull Request

1. Fork the repository and create a feature branch from `main`.
2. Write tests for any new functionality (aim for > 80 % coverage on changed code).
3. Ensure all tests, linting, and type checks pass locally.
4. Update `CHANGELOG.md` under the `[Unreleased]` section.
5. Open a pull request against `main` with a clear description.
6. Address review comments promptly.

---

## Release Process

Releases are managed by maintainers:

1. Update `__version__.py` and `CHANGELOG.md`.
2. Create and push a version tag: `git tag v0.x.y && git push origin v0.x.y`.
3. The `publish.yml` workflow publishes to PyPI automatically.

