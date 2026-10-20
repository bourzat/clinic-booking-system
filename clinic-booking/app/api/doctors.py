import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_booking_service
from app.core.db import get_session
from app.repositories import doctors as doctor_repo
from app.schemas.common import ErrorResponse
from app.schemas.doctors import AvailabilityOut, DoctorOut, SlotOut
from app.services.booking import BookingService

router = APIRouter(prefix="/doctors", tags=["doctors"])


@router.get("", response_model=list[DoctorOut])
def list_doctors(session: Session = Depends(get_session)):
    return doctor_repo.list_active(session)


@router.get(
    "/{doctor_id}/availability",
    response_model=AvailabilityOut,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
def availability(
    doctor_id: uuid.UUID,
    on: date = Query(alias="date", description="Clinic-local date, YYYY-MM-DD"),
    service: BookingService = Depends(get_booking_service),
):
    starts = service.availability(doctor_id, on)
    length = timedelta(minutes=service.settings.slot_minutes)
    return AvailabilityOut(
        doctor_id=doctor_id,
        date=on,
        timezone=service.settings.clinic_timezone,
        slot_minutes=service.settings.slot_minutes,
        slots=[SlotOut(start_at=s, end_at=s + length) for s in starts],
    )
