import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AppointmentStatus(str, enum.Enum):
    BOOKED = "booked"
    CANCELLED = "cancelled"


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        CheckConstraint("status IN ('booked', 'cancelled')", name="ck_appointments_status"),
        CheckConstraint("end_at > start_at", name="ck_appointments_order"),
        CheckConstraint(
            "(status = 'cancelled' AND cancel_reason IS NOT NULL AND cancelled_at IS NOT NULL)"
            " OR (status = 'booked' AND cancelled_at IS NULL)",
            name="ck_appointments_cancel_fields",
        ),
        # The double-booking guarantee. Only active bookings are indexed,
        # so cancelling or moving an appointment frees its slot automatically.
        Index(
            "uq_doctor_active_slot", "doctor_id", "start_at",
            unique=True, postgresql_where=text("status = 'booked'"),
        ),
        Index(
            "uq_patient_active_slot", "patient_id", "start_at",
            unique=True, postgresql_where=text("status = 'booked'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    doctor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("doctors.id"))
    patient_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("patients.id"))
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default=AppointmentStatus.BOOKED.value)
    cancel_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Optimistic locking: an UPDATE only succeeds if nobody changed the row since we read it.
    __mapper_args__ = {"version_id_col": version}

    @property
    def is_cancelled(self) -> bool:
        return self.status == AppointmentStatus.CANCELLED.value


class AppointmentEvent(Base):
    """Append-only history of what happened to an appointment."""

    __tablename__ = "appointment_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    appointment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("appointments.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(30))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
