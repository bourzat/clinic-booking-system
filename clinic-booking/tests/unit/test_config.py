import os
from unittest.mock import patch

import pytest

from app.core.config import Settings


def test_non_postgres_url():
    with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///memory"}):
        settings = Settings()
        assert settings.database_url == "sqlite:///memory"


@pytest.mark.parametrize("raw", [
    "postgres://u:p@host/db",
    "postgresql://u:p@host/db",
])
def test_postgres_urls_get_psycopg_driver(raw):
    settings = Settings(database_url=raw)
    assert settings.database_url == "postgresql+psycopg://u:p@host/db"
