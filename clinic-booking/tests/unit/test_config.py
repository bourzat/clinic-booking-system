import os
from unittest.mock import patch
from app.core.config import Settings

def test_non_postgres_url():
    with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///memory"}):
        settings = Settings()
        assert settings.database_url == "sqlite:///memory"
