import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.config import Settings
from app.services.booking import BookingService


@pytest.mark.parametrize("orig", [
    Exception("no diagnostics at all"),
    SimpleNamespace(diag=SimpleNamespace(constraint_name="some_other_constraint")),
])
def test_unknown_integrity_error_is_reraised(orig):
    service = BookingService(session=None, clock=None, settings=Settings())
    exc = IntegrityError("INSERT ...", {}, orig)
    start_at = datetime(2026, 11, 5, 9, 0, tzinfo=timezone.utc)

    with pytest.raises(IntegrityError) as caught:
        service._slot_conflict(exc, uuid.uuid4(), start_at)

    assert caught.value is exc

def test_doctor_slot_constraint_maps_to_slot_taken():
    service = BookingService(session=None, clock=None, settings=Settings())
    orig = SimpleNamespace(diag=SimpleNamespace(constraint_name="uq_doctor_active_slot"))
    exc = IntegrityError("INSERT ...", {}, orig)
    start_at = datetime(2026, 11, 5, 9, 0, tzinfo=timezone.utc)

    conflict = service._slot_conflict(exc, uuid.uuid4(), start_at)

    assert conflict.code == "SLOT_TAKEN"
