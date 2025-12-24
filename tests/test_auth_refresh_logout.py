# 리스래시 로그아웃 5개
from tests.conftest import api_post, api_get, extract_access_token, auth_header

def test_reissue_requires_cookie_401(session, base_url):
    r = api_post(session, base_url, "/api/auth/reissue")
    assert r.status_code == 401

def test_reissue_200_with_cookie(session, base_url, unique_email):
    api_post(session, base_url, "/api/users", json={
        "email": unique_email,
        "name": "테스트",
        "password": "P@ssw0rd!"
    })
    # session에 refreshToken 쿠키가 저장되도록 같은 session으로 로그인
    login = api_post(session, base_url, "/api/auth/login", json={"email": unique_email, "password": "P@ssw0rd!"})
    assert login.status_code == 200

    r = api_post(session, base_url, "/api/auth/reissue")
    assert r.status_code == 200
    at = extract_access_token(r.json())
    assert at

def test_logout_200(session, base_url, unique_email):
    api_post(session, base_url, "/api/users", json={
        "email": unique_email,
        "name": "테스트",
        "password": "P@ssw0rd!"
    })
    login = api_post(session, base_url, "/api/auth/login", json={"email": unique_email, "password": "P@ssw0rd!"})
    assert login.status_code == 200

    r = api_post(session, base_url, "/api/auth/logout")
    assert r.status_code == 200

def test_reissue_after_logout_fails_401(session, base_url, unique_email):
    api_post(session, base_url, "/api/users", json={
        "email": unique_email,
        "name": "테스트",
        "password": "P@ssw0rd!"
    })
    login = api_post(session, base_url, "/api/auth/login", json={"email": unique_email, "password": "P@ssw0rd!"})
    assert login.status_code == 200

    lo = api_post(session, base_url, "/api/auth/logout")
    assert lo.status_code == 200

    # 같은 refreshToken 쿠키로 재발급 시도 블랙리스트/DB revoke로 막힘
    r = api_post(session, base_url, "/api/auth/reissue")
    assert r.status_code == 401

def test_access_token_allows_me_even_if_refresh_missing(session, base_url, unique_email):
    api_post(session, base_url, "/api/users", json={
        "email": unique_email,
        "name": "테스트",
        "password": "P@ssw0rd!"
    })
    login = api_post(session, base_url, "/api/auth/login", json={"email": unique_email, "password": "P@ssw0rd!"})
    at = extract_access_token(login.json())

    # 쿠키 지워도 access로 /me 가능
    session.cookies.clear()
    r = api_get(session, base_url, "/api/users/me", headers=auth_header(at))
    assert r.status_code == 200