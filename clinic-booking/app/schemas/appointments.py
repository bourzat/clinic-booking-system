import uuid

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import ClinicDatetime


class AppointmentCreate(BaseModel):
    doctor_id: uuid.UUID
    patient_id: uuid.UUID
    # AwareDatetime rejects times without an offset. Guessing the zone is how appointments end up an hour off.
    start_at: AwareDatetime


class CancelRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)

    @field_validator("reason")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("reason cannot be blank")
        return value


class RescheduleRequest(BaseModel):
    start_at: AwareDatetime


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    doctor_id: uuid.UUID
    patient_id: uuid.UUID
    start_at: ClinicDatetime
    end_at: ClinicDatetime
    status: str
    cancel_reason: str | None
    cancelled_at: ClinicDatetime | None
    created_at: ClinicDatetime
