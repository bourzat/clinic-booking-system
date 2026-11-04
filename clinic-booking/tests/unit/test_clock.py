import pytest
from datetime import datetime, timezone
from app.core.clock import SystemClock, FixedClock

def test_system_clock_returns_utc_now():
    """Covers line 11 and class Protocol definitions."""
    clock = SystemClock()
    assert clock.now().tzinfo == timezone.utc

def test_fixed_clock_rejects_naive_datetime():
    """Covers line 19: ValueError when instantiated without a timezone."""
    with pytest.raises(ValueError, match="timezone-aware"):
        FixedClock(datetime(2026, 10, 20, 9, 30))
