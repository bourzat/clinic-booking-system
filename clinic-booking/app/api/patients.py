import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_booking_service
from app.core.db import get_session
from app.repositories import patients as patient_repo
from app.schemas.appointments import AppointmentOut
from app.schemas.common import ErrorResponse
from app.schemas.patients import PatientCreate, PatientOut
from app.services.booking import BookingService

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(body: PatientCreate, session: Session = Depends(get_session)):
    return patient_repo.create(session, body.full_name, body.phone, body.email)


@router.get("/{patient_id}/appointments", response_model=list[AppointmentOut], responses={404: {"model": ErrorResponse}})
def upcoming(patient_id: uuid.UUID, service: BookingService = Depends(get_booking_service)):
    return service.upcoming_for_patient(patient_id)
