import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Doctor, WorkingHours


def get_active(session: Session, doctor_id: uuid.UUID) -> Doctor | None:
    return session.scalar(select(Doctor).where(Doctor.id == doctor_id, Doctor.is_active.is_(True)))


def list_active(session: Session) -> list[Doctor]:
    return list(session.scalars(select(Doctor).where(Doctor.is_active.is_(True)).order_by(Doctor.full_name)))


def working_blocks(session: Session, doctor_id: uuid.UUID, weekday: int) -> list[WorkingHours]:
    return list(
        session.scalars(
            select(WorkingHours)
            .where(WorkingHours.doctor_id == doctor_id, WorkingHours.weekday == weekday)
            .order_by(WorkingHours.start_time)
        )
    )
