import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Appointment, AppointmentEvent, AppointmentStatus


def get(session: Session, appointment_id: uuid.UUID) -> Appointment | None:
    return session.get(Appointment, appointment_id)


def booked_starts(session: Session, doctor_id: uuid.UUID, from_at: datetime, to_at: datetime) -> set[datetime]:
    rows = session.scalars(
        select(Appointment.start_at).where(
            Appointment.doctor_id == doctor_id,
            Appointment.status == AppointmentStatus.BOOKED.value,
            Appointment.start_at >= from_at,
            Appointment.start_at < to_at,
        )
    )
    return set(rows)


def is_doctor_slot_taken(session: Session, doctor_id: uuid.UUID, start_at: datetime) -> bool:
    return session.scalar(
        select(Appointment.id).where(
            Appointment.doctor_id == doctor_id,
            Appointment.start_at == start_at,
            Appointment.status == AppointmentStatus.BOOKED.value,
        )
    ) is not None


def upcoming_for_patient(session: Session, patient_id: uuid.UUID, after: datetime) -> list[Appointment]:
    return list(
        session.scalars(
            select(Appointment)
            .where(
                Appointment.patient_id == patient_id,
                Appointment.status == AppointmentStatus.BOOKED.value,
                Appointment.start_at > after,
            )
            .order_by(Appointment.start_at)
        )
    )


def add_event(session: Session, appointment_id: uuid.UUID, event_type: str, at: datetime, payload: dict[str, Any]) -> None:
    session.add(AppointmentEvent(appointment_id=appointment_id, event_type=event_type, occurred_at=at, payload=payload))
