import uuid

from sqlalchemy.orm import Session

from app.models import Patient


def get(session: Session, patient_id: uuid.UUID) -> Patient | None:
    return session.get(Patient, patient_id)


def create(session: Session, full_name: str, phone: str, email: str | None) -> Patient:
    patient = Patient(full_name=full_name, phone=phone, email=email)
    session.add(patient)
    session.commit()
    return patient
