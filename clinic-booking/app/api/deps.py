from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.clock import Clock, SystemClock
from app.core.config import Settings, get_settings
from app.core.db import get_session
from app.services.booking import BookingService


def get_clock() -> Clock:
    return SystemClock()


def get_booking_service(
    session: Session = Depends(get_session),
    clock: Clock = Depends(get_clock),
    settings: Settings = Depends(get_settings),
) -> BookingService:
    return BookingService(session=session, clock=clock, settings=settings)
