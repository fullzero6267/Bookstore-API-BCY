# 인증 테스트 8개
from tests.conftest import api_post, api_get, extract_access_token, auth_header

def test_signup_200(session, base_url, unique_email):
    r = api_post(session, base_url, "/api/users", json={
        "email": unique_email,
        "name": "테스트",
        "password": "P@ssw0rd!"
    })
    assert r.status_code == 200
    j = r.json()
    assert j.get("isSuccess") is True
    assert j.get("payload", {}).get("email") == unique_email

def test_signup_duplicate_409(session, base_url, unique_email):
    # 먼저 1번 생성
    api_post(session, base_url, "/api/users", json={
        "email": unique_email,
        "name": "테스트",
        "password": "P@ssw0rd!"
    })
    # 같은 이메일 다시
    r2 = api_post(session, base_url, "/api/users", json={
        "email": unique_email,
        "name": "테스트",
        "password": "P@ssw0rd!"
    })
    assert r2.status_code in (409, 400)  # 네 에러코드 정책에 따라 409가 정상. 혹시 400이면 허용

def test_login_200_sets_cookie(session, base_url, unique_email):
    api_post(session, base_url, "/api/users", json={
        "email": unique_email,
        "name": "테스트",
        "password": "P@ssw0rd!"
    })
    r = api_post(session, base_url, "/api/auth/login", json={
        "email": unique_email,
        "password": "P@ssw0rd!"
    })
    assert r.status_code == 200
    assert "set-cookie" in {k.lower(): v for k, v in r.headers.items()}
    j = r.json()
    at = extract_access_token(j)
    assert at

def test_login_wrong_password_401(session, base_url, unique_email):
    api_post(session, base_url, "/api/users", json={
        "email": unique_email,
        "name": "테스트",
        "password": "P@ssw0rd!"
    })
    r = api_post(session, base_url, "/api/auth/login", json={
        "email": unique_email,
        "password": "WRONG!!"
    })
    assert r.status_code == 401

def test_login_user_not_found_404_or_401(session, base_url):
    r = api_post(session, base_url, "/api/auth/login", json={
        "email": "no_such_user_12345@example.com",
        "password": "P@ssw0rd!"
    })
    # 404 또는 401 둘 다
    assert r.status_code in (404, 401)

def test_users_me_requires_auth_401(session, base_url):
    r = api_get(session, base_url, "/api/users/me")
    assert r.status_code == 401

def test_users_me_ok_with_bearer(session, base_url, unique_email):
    api_post(session, base_url, "/api/users", json={
        "email": unique_email,
        "name": "테스트",
        "password": "P@ssw0rd!"
    })
    login = api_post(session, base_url, "/api/auth/login", json={
        "email": unique_email,
        "password": "P@ssw0rd!"
    })
    at = extract_access_token(login.json())
    r = api_get(session, base_url, "/api/users/me", headers=auth_header(at))
    assert r.status_code == 200
    j = r.json()
    assert j.get("payload", {}).get("email") == unique_email

def test_bearer_with_quotes_fails_401(session, base_url, unique_email):
    # Swagger에서 Authorization: Bearer "토큰" 처럼 따옴표 붙이면 401 나는 케이스
    api_post(session, base_url, "/api/users", json={
        "email": unique_email,
        "name": "테스트",
        "password": "P@ssw0rd!"
    })
    login = api_post(session, base_url, "/api/auth/login", json={
        "email": unique_email,
        "password": "P@ssw0rd!"
    })
    at = extract_access_token(login.json())
    r = api_get(session, base_url, "/api/users/me", headers={"Authorization": f'Bearer "{at}"'})
    assert r.status_code in (401, 403)