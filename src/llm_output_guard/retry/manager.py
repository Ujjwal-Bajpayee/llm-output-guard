"""Retry manager."""

from __future__ import annotations

import logging
from typing import Callable, Optional, Tuple, Type

from .strategies import BaseRetryStrategy, get_strategy

logger = logging.getLogger(__name__)


class RetryManager:
    """
    Coordinates retry attempts according to the chosen strategy.

    Parameters:
        max_retries:  Number of *extra* attempts after the first failure.
        strategy:     ``"fixed"`` | ``"exponential"`` | ``"linear"``.
        base_delay:   Base delay in seconds (interpretation depends on strategy).
        max_delay:    Upper bound on computed delay.
        jitter:       Add randomness to exponential back-off (default ``True``).
    """

    def __init__(
        self,
        max_retries: int = 2,
        strategy: str = "exponential",
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True,
    ) -> None:
        self.max_retries = max_retries
        self._strategy: BaseRetryStrategy = get_strategy(
            strategy, base_delay=base_delay, max_delay=max_delay, jitter=jitter
        )

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def wait(self, attempt: int) -> float:
        """
        Sleep for the appropriate delay given *attempt* number (1-based) and
        return the delay duration.
        """
        delay = self._strategy.get_delay(attempt)
        logger.debug("Retry %d/%d — waiting %.2fs.", attempt, self.max_retries, delay)
        self._strategy.sleep(attempt)
        return delay

    def get_delay(self, attempt: int) -> float:
        """Return the computed delay without sleeping."""
        return self._strategy.get_delay(attempt)

    @property
    def total_attempts(self) -> int:
        """Total attempts allowed (1 initial + max_retries)."""
        return self.max_retries + 1
