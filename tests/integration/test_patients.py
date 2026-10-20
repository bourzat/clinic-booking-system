import uuid

from tests.conftest import at


def test_create_patient(client):
    r = client.post("/patients", json={"full_name": "Wanjiku Kamau", "phone": "+254711222333"})
    assert r.status_code == 201
    assert r.json()["full_name"] == "Wanjiku Kamau"


def test_upcoming_sorted_and_excludes_cancelled(client, service, make_doctor, make_patient):
    patient = make_patient()
    doctor = make_doctor()
    later = service.book(doctor.id, patient.id, at("2026-10-21 10:00"))
    sooner = service.book(doctor.id, patient.id, at("2026-10-20 09:00"))
    gone = service.book(doctor.id, patient.id, at("2026-10-20 11:00"))
    service.cancel(gone.id, "no longer needed")

    r = client.get(f"/patients/{patient.id}/appointments")
    assert r.status_code == 200
    assert [a["id"] for a in r.json()] == [str(sooner.id), str(later.id)]


def test_upcoming_unknown_patient_is_404(client):
    assert client.get(f"/patients/{uuid.uuid4()}/appointments").status_code == 404
