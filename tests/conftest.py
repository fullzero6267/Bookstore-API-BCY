# 테스트 설정 파일
import os
import uuid
import pytest
import requests

def _base_url() -> str:
    return os.getenv("BASE_URL", "http://113.198.66.68:10099").rstrip("/")

@pytest.fixture(scope="session")
def base_url() -> str:
    return _base_url()

@pytest.fixture
def session() -> requests.Session:
    s = requests.Session()
    yield s
    s.close()

@pytest.fixture
def unique_email() -> str:
    return f"pytest_{uuid.uuid4().hex[:10]}@example.com"

def api_post(s: requests.Session, base_url: str, path: str, json=None, headers=None):
    return s.post(f"{base_url}{path}", json=json, headers=headers or {}, timeout=10)

def api_get(s: requests.Session, base_url: str, path: str, headers=None):
    return s.get(f"{base_url}{path}", headers=headers or {}, timeout=10)

def api_patch(s: requests.Session, base_url: str, path: str, json=None, headers=None):
    return s.patch(f"{base_url}{path}", json=json, headers=headers or {}, timeout=10)

def api_delete(s: requests.Session, base_url: str, path: str, headers=None):
    return s.delete(f"{base_url}{path}", headers=headers or {}, timeout=10)

def extract_access_token(resp_json: dict) -> str:
    # ApiSuccess[TokenResponse] 형태: {"isSuccess":true,"payload":{"accessToken":"..."}}
    payload = resp_json.get("payload") or {}
    return payload.get("accessToken") or ""

def auth_header(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}