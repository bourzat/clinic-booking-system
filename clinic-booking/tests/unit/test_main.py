from fastapi.testclient import TestClient
from app.main import app

def test_root_redirect():
    client = TestClient(app)
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (301, 302, 303, 307, 308)
    assert r.headers["location"] == "/docs"
