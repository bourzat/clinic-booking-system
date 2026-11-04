from unittest.mock import patch
from sqlalchemy.orm import Session

def test_health_ok(client):
    """Covers lines 20-21: successful check and environment variable resolution."""
    with patch.dict("os.environ", {"GIT_SHA": "abcd123"}):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok", "database": "ok", "commit": "abcd123"}

def test_health_db_down(client):
    """Covers lines 15-18: Exception block when the database is unreachable."""
    with patch.object(Session, "execute", side_effect=Exception("DB Down")):
        r = client.get("/health")
        assert r.status_code == 503
        assert r.json() == {"status": "unhealthy", "database": "unreachable"}
