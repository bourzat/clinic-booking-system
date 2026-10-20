import pytest

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.errors import Conflict
from app.services.booking import BookingService
from tests.conftest import TUESDAY, at


def availability(client, doctor_id):
    return [s["start_at"] for s in client.get(f"/doctors/{doctor_id}/availability", params={"date": str(TUESDAY)}).json()["slots"]]


def test_moves_appointment_and_frees_old_slot(client, service, make_doctor, make_patient):
    doctor = make_doctor()
    appt = service.book(doctor.id, make_patient().id, at("2026-10-20 09:00"))

    r = client.patch(f"/appointments/{appt.id}/reschedule", json={"start_at": "2026-10-20T14:00:00+03:00"})
    assert r.status_code == 200
    assert r.json()["id"] == str(appt.id)
    assert r.json()["start_at"] == "2026-10-20T14:00:00+03:00"

    free = availability(client, doctor.id)
    assert "2026-10-20T09:00:00+03:00" in free
    assert "2026-10-20T14:00:00+03:00" not in free


def test_taken_target_keeps_original(client, service, make_doctor, make_patient):
    doctor = make_doctor()
    mine = service.book(doctor.id, make_patient().id, at("2026-10-20 09:00"))
    service.book(doctor.id, make_patient("Other").id, at("2026-10-20 10:00"))

    r = client.patch(f"/appointments/{mine.id}/reschedule", json={"start_at": "2026-10-20T10:00:00+03:00"})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "SLOT_TAKEN"
    assert "2026-10-20T09:00:00+03:00" not in availability(client, doctor.id)  # still mine


def test_cancelled_appointment_cannot_be_rescheduled(client, service, make_doctor, make_patient):
    appt = service.book(make_doctor().id, make_patient().id, at("2026-10-20 09:00"))
    service.cancel(appt.id, "changed plans")
    r = client.patch(f"/appointments/{appt.id}/reschedule", json={"start_at": "2026-10-20T10:00:00+03:00"})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "APPOINTMENT_CANCELLED"


def test_new_slot_gets_full_validation(client, service, make_doctor, make_patient):
    appt = service.book(make_doctor().id, make_patient().id, at("2026-10-20 09:00"))
    cases = {
        "2026-10-20T12:00:00+03:00": "OUTSIDE_WORKING_HOURS",
        "2026-10-20T09:15:00+03:00": "SLOT_MISALIGNED",
        "2026-10-16T09:00:00+03:00": "BOOKING_TOO_SOON",
        "2026-10-20T09:00:00+03:00": "SAME_SLOT",
    }
    for start, code in cases.items():
        r = client.patch(f"/appointments/{appt.id}/reschedule", json={"start_at": start})
        assert r.status_code == 422, start
        assert r.json()["error"]["code"] == code


def test_concurrent_cancel_and_reschedule(service, make_doctor, make_patient):
    """Two requests read the same appointment; only the first write wins."""
    appt = service.book(make_doctor().id, make_patient().id, at("2026-10-20 09:00"))

    other_session = SessionLocal()
    try:
        other = BookingService(session=other_session, clock=service.clock, settings=get_settings())
        # The second request has already loaded the row (keep a reference so it stays in the session).
        stale = other_session.get(type(appt), appt.id)
        assert stale.status == "booked"

        service.cancel(appt.id, "first writer")

        with pytest.raises(Conflict) as exc:
            other.reschedule(appt.id, at("2026-10-20 10:00"))
        assert exc.value.code == "CONCURRENT_MODIFICATION"
    finally:
        other_session.close()
