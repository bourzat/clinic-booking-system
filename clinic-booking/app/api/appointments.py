import uuid

from fastapi import APIRouter, Depends, status

from app.api.deps import get_booking_service
from app.schemas.appointments import AppointmentCreate, AppointmentOut, CancelRequest, RescheduleRequest
from app.schemas.common import ErrorResponse
from app.services.booking import BookingService

router = APIRouter(prefix="/appointments", tags=["appointments"])

ERRORS = {404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}, 422: {"model": ErrorResponse}}


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED, responses=ERRORS)
def book(body: AppointmentCreate, service: BookingService = Depends(get_booking_service)):
    return service.book(body.doctor_id, body.patient_id, body.start_at)


@router.patch("/{appointment_id}/cancel", response_model=AppointmentOut, responses=ERRORS)
def cancel(appointment_id: uuid.UUID, body: CancelRequest, service: BookingService = Depends(get_booking_service)):
    return service.cancel(appointment_id, body.reason)


@router.patch("/{appointment_id}/reschedule", response_model=AppointmentOut, responses=ERRORS)
def reschedule(appointment_id: uuid.UUID, body: RescheduleRequest, service: BookingService = Depends(get_booking_service)):
    return service.reschedule(appointment_id, body.start_at)
