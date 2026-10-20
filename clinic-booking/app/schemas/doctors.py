import uuid
from datetime import date, time

from pydantic import BaseModel, ConfigDict

from app.schemas.common import ClinicDatetime


class WorkingBlockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    weekday: int
    start_time: time
    end_time: time


class DoctorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    full_name: str
    specialty: str
    working_hours: list[WorkingBlockOut]


class SlotOut(BaseModel):
    start_at: ClinicDatetime
    end_at: ClinicDatetime


class AvailabilityOut(BaseModel):
    doctor_id: uuid.UUID
    date: date
    timezone: str
    slot_minutes: int
    slots: list[SlotOut]
