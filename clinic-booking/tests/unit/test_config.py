from app.core.config import Settings

def test_non_postgres_url():
    # Call the classmethod directly to bypass Pydantic instantiation rules
    assert Settings.use_psycopg_driver("sqlite:///memory") == "sqlite:///memory"
