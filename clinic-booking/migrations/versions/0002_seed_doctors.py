"""Seed the clinic's 5 doctors and their weekly working hours

Revision ID: 0002
Revises: 0001

Doctor and schedule management endpoints are out of scope, so the clinic's
doctors are loaded here. IDs are fixed so they are easy to use when trying the API.
"""
import uuid
from datetime import time

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

WEEKDAYS = range(0, 5)  # Monday to Friday
FULL_DAY = [(time(8, 0), time(12, 0)), (time(13, 0), time(17, 0))]  # lunch 12:00 to 13:00
MORNINGS = [(time(8, 0), time(13, 0))]
AFTERNOONS = [(time(12, 0), time(18, 0))]

DOCTORS = [
    ("11111111-1111-1111-1111-111111111111", "Dr. Amina Odhiambo", "General Practice", {d: FULL_DAY for d in WEEKDAYS} | {5: [(time(9, 0), time(13, 0))]}),
    ("22222222-2222-2222-2222-222222222222", "Dr. Brian Mwangi", "Paediatrics", {d: FULL_DAY for d in WEEKDAYS}),
    ("33333333-3333-3333-3333-333333333333", "Dr. Cynthia Wanjiru", "Gynaecology", {d: MORNINGS for d in WEEKDAYS}),
    ("44444444-4444-4444-4444-444444444444", "Dr. David Kiprono", "Internal Medicine", {d: AFTERNOONS for d in WEEKDAYS}),
    ("55555555-5555-5555-5555-555555555555", "Dr. Esther Achieng", "Dermatology", {0: FULL_DAY, 2: FULL_DAY, 4: FULL_DAY}),
]


def upgrade() -> None:
    doctors = sa.table("doctors", sa.column("id", sa.Uuid()), sa.column("full_name"), sa.column("specialty"))
    hours = sa.table(
        "working_hours",
        sa.column("id", sa.Uuid()), sa.column("doctor_id", sa.Uuid()),
        sa.column("weekday"), sa.column("start_time"), sa.column("end_time"),
    )
    op.bulk_insert(doctors, [{"id": uuid.UUID(i), "full_name": n, "specialty": s} for i, n, s, _ in DOCTORS])
    op.bulk_insert(hours, [
        {"id": uuid.uuid4(), "doctor_id": uuid.UUID(i), "weekday": day, "start_time": start, "end_time": end}
        for i, _, _, schedule in DOCTORS
        for day, blocks in schedule.items()
        for start, end in blocks
    ])


def downgrade() -> None:
    ids = ", ".join(f"'{i}'" for i, *_ in DOCTORS)
    op.execute(f"DELETE FROM working_hours WHERE doctor_id IN ({ids})")
    op.execute(f"DELETE FROM doctors WHERE id IN ({ids})")
