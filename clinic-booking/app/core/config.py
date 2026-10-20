from functools import lru_cache
from zoneinfo import ZoneInfo

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://clinic:clinic@localhost:5432/clinic"
    clinic_timezone: str = "Africa/Nairobi"
    slot_minutes: int = 30
    min_lead_minutes: int = 60

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        # Hosting platforms usually hand out postgres:// or postgresql:// URLs.
        # SQLAlchemy needs the driver named explicitly.
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix):]
        return value

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.clinic_timezone)


@lru_cache
def get_settings() -> Settings:
    return Settings()
