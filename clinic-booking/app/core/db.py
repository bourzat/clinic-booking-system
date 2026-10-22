from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


# Server-side prepared statements break behind a transaction-mode pooler such as Neon's PgBouncer.
engine = create_engine(get_settings().database_url, pool_pre_ping=True, connect_args={"prepare_threshold": None})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
