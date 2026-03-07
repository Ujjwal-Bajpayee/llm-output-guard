"""Tests for the retry manager and strategies."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from llm_output_guard.retry.manager import RetryManager
from llm_output_guard.retry.strategies import (
    ExponentialBackoffStrategy,
    FixedRetryStrategy,
    LinearBackoffStrategy,
    get_strategy,
)


class TestFixedRetryStrategy:
    def test_constant_delay(self):
        s = FixedRetryStrategy(delay=5.0)
        assert s.get_delay(1) == 5.0
        assert s.get_delay(5) == 5.0

    def test_sleep_calls_time_sleep(self):
        s = FixedRetryStrategy(delay=1.0)
        with patch("time.sleep") as mock_sleep:
            s.sleep(1)
            mock_sleep.assert_called_once_with(1.0)


class TestExponentialBackoffStrategy:
    def test_increases_with_attempt(self):
        s = ExponentialBackoffStrategy(base_delay=1.0, jitter=False)
        assert s.get_delay(1) == 1.0
        assert s.get_delay(2) == 2.0
        assert s.get_delay(3) == 4.0

    def test_capped_at_max_delay(self):
        s = ExponentialBackoffStrategy(base_delay=1.0, max_delay=5.0, jitter=False)
        assert s.get_delay(10) == 5.0

    def test_jitter_within_bounds(self):
        s = ExponentialBackoffStrategy(base_delay=1.0, max_delay=60.0, jitter=True)
        for _ in range(20):
            delay = s.get_delay(3)
            assert 0 <= delay <= 4.0


class TestLinearBackoffStrategy:
    def test_linear_progression(self):
        s = LinearBackoffStrategy(base_delay=2.0)
        assert s.get_delay(1) == 2.0
        assert s.get_delay(2) == 4.0
        assert s.get_delay(3) == 6.0

    def test_capped_at_max_delay(self):
        s = LinearBackoffStrategy(base_delay=10.0, max_delay=15.0)
        assert s.get_delay(3) == 15.0


class TestGetStrategy:
    def test_returns_fixed(self):
        s = get_strategy("fixed")
        assert isinstance(s, FixedRetryStrategy)

    def test_returns_exponential(self):
        s = get_strategy("exponential")
        assert isinstance(s, ExponentialBackoffStrategy)

    def test_returns_linear(self):
        s = get_strategy("linear")
        assert isinstance(s, LinearBackoffStrategy)

    def test_raises_on_unknown(self):
        with pytest.raises(ValueError, match="Unknown retry strategy"):
            get_strategy("foobar")


class TestRetryManager:
    def test_total_attempts(self):
        rm = RetryManager(max_retries=4)
        assert rm.total_attempts == 5

    def test_wait_returns_delay(self):
        rm = RetryManager(max_retries=3, strategy="fixed", base_delay=0.1)
        with patch("time.sleep"):
            delay = rm.wait(1)
        assert delay == pytest.approx(0.1)

    def test_get_delay_no_sleep(self):
        rm = RetryManager(max_retries=3, strategy="fixed", base_delay=2.0)
        assert rm.get_delay(1) == 2.0
