import os
import uuid
from datetime import datetime, time
from zoneinfo import ZoneInfo

# Point the app at the test database before anything imports the engine.
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://clinic:clinic@localhost:5432/clinic_test"
)

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.api.deps import get_clock  # noqa: E402
from app.core.clock import FixedClock  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.core.db import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Doctor, Patient, WorkingHours  # noqa: E402
from app.services.booking import BookingService  # noqa: E402

TZ = ZoneInfo("Africa/Nairobi")
# Monday 19 Oct 2026, 06:00 in Nairobi. Tuesday 20 Oct is used as "a normal future day".
NOW = datetime(2026, 10, 19, 6, 0, tzinfo=TZ)
TUESDAY = datetime(2026, 10, 20).date()


def at(day_hour: str) -> datetime:
    """at('2026-10-20 09:30') -> aware datetime in clinic time."""
    return datetime.fromisoformat(day_hour).replace(tzinfo=TZ)


@pytest.fixture(scope="session", autouse=True)
def database():
    """Build the schema with the real migrations, so the migrations are tested too."""
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "..", "migrations"))
    command.upgrade(cfg, "head")
    yield


@pytest.fixture(autouse=True)
def clean_tables():
    # Start every test from an empty clinic (seeded doctors removed too) so tests control their own data.
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE appointment_events, appointments, patients, working_hours, doctors CASCADE"))
    yield


@pytest.fixture
def session():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture
def clock():
    return FixedClock(NOW)


@pytest.fixture
def service(session, clock):
    return BookingService(session=session, clock=clock, settings=get_settings())


@pytest.fixture
def client(clock):
    app.dependency_overrides[get_clock] = lambda: clock
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


DEFAULT_SCHEDULE = {d: [(time(8), time(12)), (time(13), time(17))] for d in range(5)}


@pytest.fixture
def make_doctor(session):
    def _make(schedule=None, active=True) -> Doctor:
        doctor = Doctor(id=uuid.uuid4(), full_name="Dr. Test", specialty="General", is_active=active)
        session.add(doctor)
        for weekday, blocks in (schedule or DEFAULT_SCHEDULE).items():
            for start, end in blocks:
                session.add(WorkingHours(doctor_id=doctor.id, weekday=weekday, start_time=start, end_time=end))
        session.commit()
        return doctor
    return _make


@pytest.fixture
def make_patient(session):
    def _make(name="Jane Patient") -> Patient:
        patient = Patient(full_name=name, phone="+254700000000")
        session.add(patient)
        session.commit()
        return patient
    return _make
