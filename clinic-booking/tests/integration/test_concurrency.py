import threading
from concurrent.futures import ThreadPoolExecutor

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.errors import Conflict
from app.services.booking import BookingService
from tests.conftest import at


def test_only_one_of_many_simultaneous_bookings_wins(make_doctor, make_patient, clock):
    doctor = make_doctor()
    patients = [make_patient(f"P{i}") for i in range(10)]
    start = at("2026-10-20 09:00")
    barrier = threading.Barrier(len(patients))

    def attempt(patient_id):
        session = SessionLocal()
        try:
            svc = BookingService(session=session, clock=clock, settings=get_settings())
            barrier.wait()  # release all requests at the same moment
            svc.book(doctor.id, patient_id, start)
            return "booked"
        except Conflict as exc:
            return exc.code
        finally:
            session.close()

    with ThreadPoolExecutor(max_workers=len(patients)) as pool:
        results = list(pool.map(attempt, [p.id for p in patients]))

    assert results.count("booked") == 1
    assert all(r == "SLOT_TAKEN" for r in results if r != "booked")
