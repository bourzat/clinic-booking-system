from app.api.deps import get_clock
from app.core.clock import SystemClock

def test_get_clock():
    assert isinstance(get_clock(), SystemClock)
