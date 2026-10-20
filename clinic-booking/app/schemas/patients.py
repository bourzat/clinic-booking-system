import uuid

from pydantic import BaseModel, ConfigDict, Field


class PatientCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    phone: str = Field(min_length=7, max_length=30)
    email: str | None = Field(default=None, max_length=254)


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    full_name: str
    phone: str
    email: str | None
