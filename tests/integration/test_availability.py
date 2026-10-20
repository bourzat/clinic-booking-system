import uuid

from tests.conftest import TUESDAY, at


def test_returns_all_slots_for_free_day(client, make_doctor):
    doctor = make_doctor()
    r = client.get(f"/doctors/{doctor.id}/availability", params={"date": str(TUESDAY)})
    assert r.status_code == 200
    body = r.json()
    assert len(body["slots"]) == 16
    assert body["slots"][0] == {"start_at": "2026-10-20T08:00:00+03:00", "end_at": "2026-10-20T08:30:00+03:00"}
    assert body["timezone"] == "Africa/Nairobi"


def test_booked_slot_is_removed(client, make_doctor, make_patient, service):
    doctor, patient = make_doctor(), make_patient()
    service.book(doctor.id, patient.id, at("2026-10-20 09:00"))
    starts = [s["start_at"] for s in client.get(f"/doctors/{doctor.id}/availability", params={"date": str(TUESDAY)}).json()["slots"]]
    assert "2026-10-20T09:00:00+03:00" not in starts
    assert len(starts) == 15


def test_today_hides_slots_inside_lead_time(client, make_doctor):
    # NOW is Monday 06:00, so 08:00 onwards is bookable but anything before 07:00 would not be.
    doctor = make_doctor()
    slots = client.get(f"/doctors/{doctor.id}/availability", params={"date": "2026-10-19"}).json()["slots"]
    assert slots[0]["start_at"] == "2026-10-19T08:00:00+03:00"


def test_day_off_and_past_date_return_empty(client, make_doctor):
    doctor = make_doctor()
    assert client.get(f"/doctors/{doctor.id}/availability", params={"date": "2026-10-25"}).json()["slots"] == []  # Sunday
    assert client.get(f"/doctors/{doctor.id}/availability", params={"date": "2026-10-01"}).json()["slots"] == []


def test_unknown_doctor_is_404(client):
    r = client.get(f"/doctors/{uuid.uuid4()}/availability", params={"date": str(TUESDAY)})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "DOCTOR_NOT_FOUND"


def test_missing_or_bad_date_is_422(client, make_doctor):
    doctor = make_doctor()
    assert client.get(f"/doctors/{doctor.id}/availability").status_code == 422
    r = client.get(f"/doctors/{doctor.id}/availability", params={"date": "20-10-2026"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"
