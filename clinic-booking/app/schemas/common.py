from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, PlainSerializer

from app.core.config import get_settings


def _to_clinic_time(value: datetime) -> str:
    return value.astimezone(get_settings().tz).isoformat()


# Datetimes are stored in UTC and shown to clients in clinic local time with an offset.
ClinicDatetime = Annotated[datetime, PlainSerializer(_to_clinic_time, return_type=str)]


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = {}


class ErrorResponse(BaseModel):
    error: ErrorBody
