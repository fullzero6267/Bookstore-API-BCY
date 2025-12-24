# 사용자 테스트 5개
from tests.conftest import api_post, api_get, api_patch, api_delete, extract_access_token, auth_header

def test_patch_me_200(session, base_url, unique_email):
    api_post(session, base_url, "/api/users", json={
        "email": unique_email,
        "name": "테스트",
        "password": "P@ssw0rd!"
    })
    login = api_post(session, base_url, "/api/auth/login", json={"email": unique_email, "password": "P@ssw0rd!"})
    at = extract_access_token(login.json())

    r = api_patch(session, base_url, "/api/users/me", json={"name": "변경됨"}, headers=auth_header(at))
    assert r.status_code == 200
    assert r.json().get("payload", {}).get("name") == "변경됨"

def test_patch_me_requires_auth_401(session, base_url):
    r = api_patch(session, base_url, "/api/users/me", json={"name": "x"})
    assert r.status_code == 401

def test_soft_delete_200(session, base_url, unique_email):
    api_post(session, base_url, "/api/users", json={
        "email": unique_email,
        "name": "테스트",
        "password": "P@ssw0rd!"
    })
    login = api_post(session, base_url, "/api/auth/login", json={"email": unique_email, "password": "P@ssw0rd!"})
    at = extract_access_token(login.json())

    r = api_delete(session, base_url, "/api/users/me/soft-delete", headers=auth_header(at))
    assert r.status_code == 200

def test_soft_deleted_user_cannot_use_me_401(session, base_url, unique_email):
    api_post(session, base_url, "/api/users", json={
        "email": unique_email,
        "name": "테스트",
        "password": "P@ssw0rd!"
    })
    login = api_post(session, base_url, "/api/auth/login", json={"email": unique_email, "password": "P@ssw0rd!"})
    at = extract_access_token(login.json())

    api_delete(session, base_url, "/api/users/me/soft-delete", headers=auth_header(at))

    r = api_get(session, base_url, "/api/users/me", headers=auth_header(at))
    assert r.status_code == 401

def test_permanent_delete_200(session, base_url, unique_email):
    api_post(session, base_url, "/api/users", json={
        "email": unique_email,
        "name": "테스트",
        "password": "P@ssw0rd!"
    })
    login = api_post(session, base_url, "/api/auth/login", json={"email": unique_email, "password": "P@ssw0rd!"})
    at = extract_access_token(login.json())

    r = api_delete(session, base_url, "/api/users/me/permanent", headers=auth_header(at))
    assert r.status_code == 200