"""All booking rules live here. Nothing in this module knows about HTTP."""

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.core.clock import Clock
from app.core.config import Settings
from app.core.errors import Conflict, NotFound, RuleViolation
from app.models import Appointment, AppointmentStatus, Doctor
from app.repositories import appointments as appt_repo
from app.repositories import doctors as doctor_repo
from app.repositories import patients as patient_repo
from app.services.slots import Block, classify_start, generate_slots


@dataclass
class BookingService:
    session: Session
    clock: Clock
    settings: Settings

    # ---------- queries ----------

    def availability(self, doctor_id: uuid.UUID, day: date) -> list[datetime]:
        self._require_doctor(doctor_id)
        tz = self.settings.tz
        blocks = self._blocks(doctor_id, day.weekday())
        all_slots = generate_slots(blocks, day, tz, self.settings.slot_minutes)
        if not all_slots:
            return []

        day_start = datetime.combine(day, datetime.min.time(), tzinfo=tz)
        taken = appt_repo.booked_starts(self.session, doctor_id, day_start, day_start + timedelta(days=1))
        earliest = self._earliest_bookable()
        return [s for s in all_slots if s not in taken and s >= earliest]

    def upcoming_for_patient(self, patient_id: uuid.UUID) -> list[Appointment]:
        self._require_patient(patient_id)
        return appt_repo.upcoming_for_patient(self.session, patient_id, self.clock.now())

    # ---------- commands ----------

    def book(self, doctor_id: uuid.UUID, patient_id: uuid.UUID, start_at: datetime) -> Appointment:
        self._require_doctor(doctor_id)
        self._require_patient(patient_id)
        self._validate_slot(doctor_id, start_at)

        appointment = Appointment(
            doctor_id=doctor_id,
            patient_id=patient_id,
            start_at=start_at,
            end_at=start_at + self._slot_length(),
            status=AppointmentStatus.BOOKED.value,
        )
        self.session.add(appointment)
        try:
            self.session.flush()
            appt_repo.add_event(self.session, appointment.id, "created", self.clock.now(),
                                {"start_at": start_at.isoformat()})
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise self._slot_conflict(exc, doctor_id, start_at) from exc
        return appointment

    def cancel(self, appointment_id: uuid.UUID, reason: str) -> Appointment:
        appointment = self._require_appointment(appointment_id)
        if appointment.is_cancelled:
            raise Conflict("ALREADY_CANCELLED", "This appointment is already cancelled.",
                           {"cancelled_at": appointment.cancelled_at.isoformat()})
        self._require_not_past(appointment)

        now = self.clock.now()
        appointment.status = AppointmentStatus.CANCELLED.value
        appointment.cancel_reason = reason
        appointment.cancelled_at = now
        try:
            appt_repo.add_event(self.session, appointment.id, "cancelled", now, {"reason": reason})
            self.session.commit()
        except StaleDataError as exc:
            self.session.rollback()
            raise self._concurrent_edit() from exc
        return appointment

    def reschedule(self, appointment_id: uuid.UUID, new_start_at: datetime) -> Appointment:
        appointment = self._require_appointment(appointment_id)
        if appointment.is_cancelled:
            raise Conflict("APPOINTMENT_CANCELLED", "A cancelled appointment cannot be rescheduled. Book a new one instead.")
        self._require_not_past(appointment)
        if new_start_at == appointment.start_at:
            raise RuleViolation("SAME_SLOT", "The new time is the same as the current one.")
        self._validate_slot(appointment.doctor_id, new_start_at)

        old_start = appointment.start_at
        appointment.start_at = new_start_at
        appointment.end_at = new_start_at + self._slot_length()
        try:
            self.session.flush()
            appt_repo.add_event(self.session, appointment.id, "rescheduled", self.clock.now(),
                                {"from": old_start.isoformat(), "to": new_start_at.isoformat()})
            self.session.commit()
        except IntegrityError as exc:
            # Transaction rolls back: the patient keeps the original slot.
            self.session.rollback()
            raise self._slot_conflict(exc, appointment.doctor_id, new_start_at) from exc
        except StaleDataError as exc:
            self.session.rollback()
            raise self._concurrent_edit() from exc
        return appointment

    # ---------- rules ----------

    def _validate_slot(self, doctor_id: uuid.UUID, start_at: datetime) -> None:
        """Checks shared by booking and rescheduling, so the two can never drift apart."""
        local = start_at.astimezone(self.settings.tz)
        verdict = classify_start(local, self._blocks(doctor_id, local.weekday()), self.settings.slot_minutes)

        if verdict == "misaligned":
            raise RuleViolation(
                "SLOT_MISALIGNED",
                f"Appointments start on {self.settings.slot_minutes}-minute boundaries within the doctor's working hours.",
                {"start_at": local.isoformat()},
            )
        if start_at < self._earliest_bookable():
            raise RuleViolation(
                "BOOKING_TOO_SOON",
                f"Appointments must be booked at least {self.settings.min_lead_minutes} minutes in advance.",
                {"start_at": local.isoformat(), "earliest_allowed": self._earliest_bookable().astimezone(self.settings.tz).isoformat()},
            )
        if verdict == "outside":
            raise RuleViolation(
                "OUTSIDE_WORKING_HOURS",
                "The doctor is not working at that time.",
                {"start_at": local.isoformat()},
            )
        # Friendly pre-check for the common case. The unique index is what actually guarantees it.
        if appt_repo.is_doctor_slot_taken(self.session, doctor_id, start_at):
            raise Conflict("SLOT_TAKEN", "That slot is already booked. Please pick another time.",
                           {"start_at": local.isoformat()})

    def _require_not_past(self, appointment: Appointment) -> None:
        if appointment.start_at <= self.clock.now():
            raise RuleViolation("APPOINTMENT_IN_PAST", "Past appointments cannot be changed.")

    # ---------- helpers ----------

    def _require_doctor(self, doctor_id: uuid.UUID) -> Doctor:
        doctor = doctor_repo.get_active(self.session, doctor_id)
        if doctor is None:
            raise NotFound("DOCTOR_NOT_FOUND", "No active doctor with that ID.", {"doctor_id": str(doctor_id)})
        return doctor

    def _require_patient(self, patient_id: uuid.UUID) -> None:
        if patient_repo.get(self.session, patient_id) is None:
            raise NotFound("PATIENT_NOT_FOUND", "No patient with that ID.", {"patient_id": str(patient_id)})

    def _require_appointment(self, appointment_id: uuid.UUID) -> Appointment:
        appointment = appt_repo.get(self.session, appointment_id)
        if appointment is None:
            raise NotFound("APPOINTMENT_NOT_FOUND", "No appointment with that ID.",
                           {"appointment_id": str(appointment_id)})
        return appointment

    def _blocks(self, doctor_id: uuid.UUID, weekday: int) -> list[Block]:
        return [Block(w.start_time, w.end_time) for w in doctor_repo.working_blocks(self.session, doctor_id, weekday)]

    def _slot_length(self) -> timedelta:
        return timedelta(minutes=self.settings.slot_minutes)

    def _earliest_bookable(self) -> datetime:
        return self.clock.now() + timedelta(minutes=self.settings.min_lead_minutes)

    def _slot_conflict(self, exc: IntegrityError, doctor_id: uuid.UUID, start_at: datetime) -> Conflict:
        constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
        details = {"start_at": start_at.astimezone(self.settings.tz).isoformat()}
        if constraint == "uq_patient_active_slot":
            return Conflict("PATIENT_DOUBLE_BOOKED", "This patient already has an appointment at that time.", details)
        if constraint == "uq_doctor_active_slot":
            return Conflict("SLOT_TAKEN", "That slot was just booked by someone else. Please pick another time.", details)
        raise exc

    @staticmethod
    def _concurrent_edit() -> Conflict:
        return Conflict("CONCURRENT_MODIFICATION",
                        "This appointment was changed by another request. Reload it and try again.")
