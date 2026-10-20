import uuid
from datetime import time

import pytest

from app.core.errors import RuleViolation
from tests.conftest import at


def book(client, doctor_id, patient_id, start):
    return client.post("/appointments", json={"doctor_id": str(doctor_id), "patient_id": str(patient_id), "start_at": start})


def test_books_a_free_slot(client, make_doctor, make_patient):
    doctor, patient = make_doctor(), make_patient()
    r = book(client, doctor.id, patient.id, "2026-10-20T09:30:00+03:00")
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "booked"
    assert body["start_at"] == "2026-10-20T09:30:00+03:00"
    assert body["end_at"] == "2026-10-20T10:00:00+03:00"


def test_accepts_utc_input_for_the_same_slot(client, make_doctor, make_patient):
    doctor, patient = make_doctor(), make_patient()
    r = book(client, doctor.id, patient.id, "2026-10-20T06:30:00Z")
    assert r.status_code == 201
    assert r.json()["start_at"] == "2026-10-20T09:30:00+03:00"


def test_taken_slot_is_409(client, make_doctor, make_patient):
    doctor = make_doctor()
    assert book(client, doctor.id, make_patient().id, "2026-10-20T09:30:00+03:00").status_code == 201
    r = book(client, doctor.id, make_patient("Other").id, "2026-10-20T09:30:00+03:00")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "SLOT_TAKEN"


def test_patient_cannot_be_in_two_places(client, make_doctor, make_patient):
    patient = make_patient()
    assert book(client, make_doctor().id, patient.id, "2026-10-20T09:30:00+03:00").status_code == 201
    r = book(client, make_doctor().id, patient.id, "2026-10-20T09:30:00+03:00")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "PATIENT_DOUBLE_BOOKED"


def test_outside_working_hours_is_422(client, make_doctor, make_patient):
    doctor, patient = make_doctor(), make_patient()
    for start in ("2026-10-20T12:00:00+03:00", "2026-10-20T17:00:00+03:00", "2026-10-25T09:00:00+03:00"):
        r = book(client, doctor.id, patient.id, start)
        assert r.status_code == 422, start
        assert r.json()["error"]["code"] == "OUTSIDE_WORKING_HOURS"


def test_misaligned_start_is_422(client, make_doctor, make_patient):
    r = book(client, make_doctor().id, make_patient().id, "2026-10-20T09:10:00+03:00")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "SLOT_MISALIGNED"


def test_past_time_is_422(client, make_doctor, make_patient):
    r = book(client, make_doctor().id, make_patient().id, "2026-10-16T09:00:00+03:00")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "BOOKING_TOO_SOON"


def test_lead_time_boundary(service, make_doctor, make_patient, clock):
    # Doctor works from 06:30 on Monday so we can probe the 1-hour edge around NOW (06:00).
    doctor = make_doctor({0: [(time(6, 30), time(9))]})
    patient = make_patient()
    with pytest.raises(RuleViolation) as exc:
        service.book(doctor.id, patient.id, at("2026-10-19 06:30"))  # 30 min ahead
    assert exc.value.code == "BOOKING_TOO_SOON"
    assert service.book(doctor.id, patient.id, at("2026-10-19 07:00")).status == "booked"  # exactly 60 min


def test_naive_datetime_is_rejected(client, make_doctor, make_patient):
    r = book(client, make_doctor().id, make_patient().id, "2026-10-20T09:30:00")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_unknown_doctor_or_patient_is_404(client, make_doctor, make_patient):
    assert book(client, uuid.uuid4(), make_patient().id, "2026-10-20T09:30:00+03:00").json()["error"]["code"] == "DOCTOR_NOT_FOUND"
    assert book(client, make_doctor().id, uuid.uuid4(), "2026-10-20T09:30:00+03:00").json()["error"]["code"] == "PATIENT_NOT_FOUND"


def test_inactive_doctor_is_404(client, make_doctor, make_patient):
    r = book(client, make_doctor(active=False).id, make_patient().id, "2026-10-20T09:30:00+03:00")
    assert r.status_code == 404
