#!/usr/bin/env python
"""
scripts/benchmark.py — micro-benchmark for llm-output-guard's validation throughput.

Usage:
    python scripts/benchmark.py [--iterations N]
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from typing import Any, Dict

from llm_output_guard import Validator


SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "email": {"type": "string"},
    },
    "required": ["name", "age"],
}

VALID_OUTPUT = json.dumps({"name": "Alice", "age": 30, "email": "alice@example.com"})
INVALID_OUTPUT = json.dumps({"name": "Bob"})  # missing 'age'


def bench_validate_output(n: int) -> None:
    validator = Validator(schema=SCHEMA)
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        validator.validate_output(VALID_OUTPUT)
        times.append(time.perf_counter() - t0)

    avg_ms = statistics.mean(times) * 1_000
    p99_ms = sorted(times)[int(0.99 * len(times))] * 1_000
    ops = 1 / statistics.mean(times)
    print(f"validate_output  |  avg={avg_ms:.3f}ms  p99={p99_ms:.3f}ms  {ops:,.0f} ops/s  (n={n})")


def bench_json_extraction(n: int) -> None:
    from llm_output_guard.utils.json_helpers import extract_json

    wrapped = f"Here is the answer: {VALID_OUTPUT} — that's it."
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        extract_json(wrapped)
        times.append(time.perf_counter() - t0)

    avg_ms = statistics.mean(times) * 1_000
    p99_ms = sorted(times)[int(0.99 * len(times))] * 1_000
    ops = 1 / statistics.mean(times)
    print(f"extract_json     |  avg={avg_ms:.3f}ms  p99={p99_ms:.3f}ms  {ops:,.0f} ops/s  (n={n})")


def main() -> None:
    parser = argparse.ArgumentParser(description="llm-output-guard benchmark")
    parser.add_argument("--iterations", "-n", type=int, default=10_000)
    args = parser.parse_args()

    n = args.iterations
    print(f"Running {n:,} iterations per benchmark...\n")
    bench_validate_output(n)
    bench_json_extraction(n)
    print("\nDone.")


if __name__ == "__main__":
    main()
