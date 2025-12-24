# health 테스트 3개
from tests.conftest import api_get

def test_health_200(session, base_url):
    r = api_get(session, base_url, "/health")
    assert r.status_code == 200

def test_health_json(session, base_url):
    r = api_get(session, base_url, "/health")
    assert r.headers.get("content-type", "").startswith("application/json")
    j = r.json()
    assert isinstance(j, dict)

def test_docs_200(session, base_url):
    r = session.get(f"{base_url}/docs", timeout=10)
    assert r.status_code == 200