import uuid
from datetime import timedelta

from app.core.clock import FixedClock
from tests.conftest import NOW, at


def test_cancel_frees_the_slot(client, service, make_doctor, make_patient):
    doctor = make_doctor()
    appt = service.book(doctor.id, make_patient().id, at("2026-10-20 09:00"))

    r = client.patch(f"/appointments/{appt.id}/cancel", json={"reason": "Feeling better"})
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"
    assert r.json()["cancel_reason"] == "Feeling better"

    # Same slot can be booked again by someone else.
    again = client.post("/appointments", json={
        "doctor_id": str(doctor.id), "patient_id": str(make_patient("Next").id), "start_at": "2026-10-20T09:00:00+03:00",
    })
    assert again.status_code == 201


def test_cancel_twice_is_409(client, service, make_doctor, make_patient):
    appt = service.book(make_doctor().id, make_patient().id, at("2026-10-20 09:00"))
    client.patch(f"/appointments/{appt.id}/cancel", json={"reason": "x"})
    r = client.patch(f"/appointments/{appt.id}/cancel", json={"reason": "again"})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "ALREADY_CANCELLED"


def test_reason_is_required(client, service, make_doctor, make_patient):
    appt = service.book(make_doctor().id, make_patient().id, at("2026-10-20 09:00"))
    assert client.patch(f"/appointments/{appt.id}/cancel", json={}).status_code == 422
    assert client.patch(f"/appointments/{appt.id}/cancel", json={"reason": "   "}).status_code == 422


def test_unknown_appointment_is_404(client):
    r = client.patch(f"/appointments/{uuid.uuid4()}/cancel", json={"reason": "x"})
    assert r.status_code == 404


def test_past_appointment_cannot_be_cancelled(client, service, make_doctor, make_patient, clock):
    appt = service.book(make_doctor().id, make_patient().id, at("2026-10-20 09:00"))
    clock._at = NOW + timedelta(days=3)
    r = client.patch(f"/appointments/{appt.id}/cancel", json={"reason": "late"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "APPOINTMENT_IN_PAST"
