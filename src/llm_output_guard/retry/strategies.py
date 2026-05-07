"""Retry strategies for llm-output-guard."""

from __future__ import annotations

import random
import time


class BaseRetryStrategy:
    """Abstract base class for retry strategies."""

    def get_delay(self, attempt: int) -> float:
        raise NotImplementedError

    def sleep(self, attempt: int) -> None:
        time.sleep(self.get_delay(attempt))


class FixedRetryStrategy(BaseRetryStrategy):
    """Wait a constant *delay* seconds between every retry."""

    def __init__(self, delay: float = 1.0) -> None:
        self.delay = delay

    def get_delay(self, attempt: int) -> float:
        return self.delay


class ExponentialBackoffStrategy(BaseRetryStrategy):
    """
    Exponential back-off: ``base_delay * 2 ** (attempt - 1)``, capped at
    *max_delay*, with optional full jitter.
    """

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True,
    ) -> None:
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        delay: float = min(self.base_delay * (2 ** (attempt - 1)), self.max_delay)
        if self.jitter:
            delay = random.uniform(0, delay)
        return delay


class LinearBackoffStrategy(BaseRetryStrategy):
    """Linear back-off: ``base_delay * attempt``."""

    def __init__(self, base_delay: float = 1.0, max_delay: float = 60.0) -> None:
        self.base_delay = base_delay
        self.max_delay = max_delay

    def get_delay(self, attempt: int) -> float:
        return min(self.base_delay * attempt, self.max_delay)


def get_strategy(
    name: str,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
) -> BaseRetryStrategy:
    """Factory: return a strategy instance from its string name."""
    strategies = {
        "fixed": FixedRetryStrategy(delay=base_delay),
        "exponential": ExponentialBackoffStrategy(
            base_delay=base_delay, max_delay=max_delay, jitter=jitter
        ),
        "linear": LinearBackoffStrategy(base_delay=base_delay, max_delay=max_delay),
    }
    if name not in strategies:
        raise ValueError(f"Unknown retry strategy {name!r}. Choose from: {list(strategies)}")
    return strategies[name]
