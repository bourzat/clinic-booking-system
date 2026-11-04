from app.core.config import Settings

def test_non_postgres_url():
    # model_validate runs all validators on the provided dictionary
    settings = Settings.model_validate({"database_url": "sqlite:///memory"})
    assert settings.database_url == "sqlite:///memory"
