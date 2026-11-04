from app.core.config import Settings

def test_non_postgres_url():
    settings = Settings(database_url="sqlite:///memory")
    assert settings.database_url == "sqlite:///memory"
