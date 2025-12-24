"""
인증
Auth API
로그인: access / refresh 발급
재발급: refresh로 access / refresh 재발급
로그아웃: refresh 폐기
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid
import os
import secrets
import requests

from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Depends, Request
from fastapi import Response
from app.core.redis_client import get_redis
from sqlalchemy.orm import Session

from app.db.session import get_db                 # DB 세션
from app.models.user import User
from app.models.refresh_token import RefreshToken # refresh token 저장 테이블
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.response import ApiSuccess
from app.schemas.openapi_examples import COMMON_ERROR_RESPONSES
from app.core.security import (
    verify_password,                              # 비밀번호 검증
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.errors import (
    raise_not_found,
    raise_unauthorized,
    raise_bad_request,
)

router = APIRouter(prefix="/auth", tags=["Auth"], responses=COMMON_ERROR_RESPONSES)

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")
NAVER_REDIRECT_URI = os.getenv("NAVER_REDIRECT_URI", "")  # 예: http://113.198.66.68:10099/api/auth/naver/callback

NAVER_AUTH_URL = "https://nid.naver.com/oauth2.0/authorize"
NAVER_TOKEN_URL = "https://nid.naver.com/oauth2.0/token"
NAVER_PROFILE_URL = "https://openapi.naver.com/v1/nid/me"


def _make_dummy_email(provider: str, provider_id: str) -> str:
    # 이메일 제공 안 되는 케이스 대비 (DB에서 email UNIQUE/NOT NULL이면 특히 필요)
    return f"{provider.lower()}_{provider_id}@{provider.lower()}.local"

@router.get("/naver", summary="네이버 로그인 시작")
def naver_login(request: Request):
    if not NAVER_CLIENT_ID or not NAVER_REDIRECT_URI:
        raise_bad_request("NAVER env 가 설정되지 않았습니다.", "BAD_REQUEST")

    state = secrets.token_urlsafe(16)

    # (권장) state 검증: redis에 5분 저장
    r = get_redis()
    r.setex(f"oauth:naver:state:{state}", 300, "1")

    url = (
        f"{NAVER_AUTH_URL}"
        f"?response_type=code"
        f"&client_id={NAVER_CLIENT_ID}"
        f"&redirect_uri={NAVER_REDIRECT_URI}"
        f"&state={state}"
    )
    return RedirectResponse(url)

@router.get("/naver/callback", response_model=ApiSuccess[TokenResponse], summary="네이버 로그인 콜백")
def naver_callback(
    request: Request,
    response: Response,
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET or not NAVER_REDIRECT_URI:
        raise_bad_request("NAVER env 가 설정되지 않았습니다.", "BAD_REQUEST")

    # state 검증
    r = get_redis()
    if r.get(f"oauth:naver:state:{state}") != "1":
        raise_unauthorized("state 가 유효하지 않습니다.", "UNAUTHORIZED")
    r.delete(f"oauth:naver:state:{state}")

    #  code  네이버 access_token 교환
    token_res = requests.get(
        NAVER_TOKEN_URL,
        params={
            "grant_type": "authorization_code",
            "client_id": NAVER_CLIENT_ID,
            "client_secret": NAVER_CLIENT_SECRET,
            "code": code,
            "state": state,
        },
        timeout=5,
    )
    if token_res.status_code != 200:
        raise_unauthorized("네이버 토큰 발급 실패", "UNAUTHORIZED")

    token_json = token_res.json()
    naver_access = token_json.get("access_token")
    if not naver_access:
        raise_unauthorized("네이버 토큰 발급 실패", "UNAUTHORIZED")

    # 프로필 조회
    prof_res = requests.get(
        NAVER_PROFILE_URL,
        headers={"Authorization": f"Bearer {naver_access}"},
        timeout=5,
    )
    if prof_res.status_code != 200:
        raise_unauthorized("네이버 프로필 조회 실패", "UNAUTHORIZED")

    prof = prof_res.json() or {}
    info = prof.get("response") or {}
    provider_id = info.get("id")  # 네이버 고유 ID (핵심)
    email = info.get("email")     # 없을 수 있음
    name = info.get("name") or info.get("nickname") or "NAVER_USER"

    if not provider_id:
        raise_unauthorized("네이버 프로필 id가 없습니다.", "UNAUTHORIZED")

    # 유저 찾기/생성
    # User 모델에 provider/provider_id 컬럼이 있으면 그걸로 찾기
    # 없으면 email로만 처리(이메일 없으면 더미 생성)
    user = None

    if hasattr(User, "provider") and hasattr(User, "provider_id"):
        user = (
            db.query(User)
            .filter(User.provider == "NAVER", User.provider_id == provider_id)
            .first()
        )
        if not user:
            if not email:
                email = _make_dummy_email("NAVER", provider_id)

            user = User(
                email=email,
                password_hash="SOCIAL_LOGIN",  # 소셜은 패스워드 사용 안 함(모델 NOT NULL 방어용)
                name=name,
                role="ROLE_USER",
                is_active=True,
                provider="NAVER",
                provider_id=provider_id,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
    else:
        # provider 컬럼이 없으면 email 기반으로만 처리
        if not email:
            email = _make_dummy_email("NAVER", provider_id)

        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                password_hash="SOCIAL_LOGIN",
                name=name,
                role="ROLE_USER",
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

    # 5) 우리 서비스 JWT 발급 + refresh 저장(기존 로그인과 동일 정책)
    access_token = create_access_token(subject=str(user.id), role=user.role)

    jti = uuid.uuid4().hex
    refresh_token = create_refresh_token(subject=str(user.id), jti=jti)

    response.set_cookie(
        key="refreshToken",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=14 * 24 * 3600,
    )

    expires_at = datetime.now(timezone.utc) + timedelta(days=14)
    db.add(
        RefreshToken(
            user_id=user.id,
            jti=jti,
            expires_at=expires_at,
            is_revoked=False,
        )
    )
    db.commit()

    return ApiSuccess(
        message="네이버 로그인 성공",
        payload=TokenResponse(accessToken=access_token, refreshToken=refresh_token),
    )

def _get_refresh_from_request(request: Request) -> str | None:
    # 과제 구현: refresh token은 쿠키로만 받음
    return request.cookies.get("refreshToken") or request.cookies.get("refresh_token")


@router.post("/login", response_model=ApiSuccess[TokenResponse], summary="로그인")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise_not_found("유저를 찾을 수 없습니다.", "USER_NOT_FOUND")

    if not verify_password(payload.password, user.password_hash):
        raise_unauthorized("이메일 또는 비밀번호가 올바르지 않습니다.", "INVALID_CREDENTIALS")

    if hasattr(user, "is_active") and not user.is_active:
        raise_unauthorized("비활성화된 계정입니다.", "USER_INACTIVE")

    access_token = create_access_token(            # access token 발급
        subject=str(user.id),
        role=user.role
    )

    jti = uuid.uuid4().hex                         # refresh token 식별자
    refresh_token = create_refresh_token(
        subject=str(user.id),
        jti=jti
    )

    response.set_cookie(
        key="refreshToken",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=False,  # JCloud HTTPS면 True 권장
        max_age=14 * 24 * 3600,
    )

    expires_at = datetime.now(timezone.utc) + timedelta(days=14)
    db.add(
        RefreshToken(                              # refresh token 서버 저장
            user_id=user.id,
            jti=jti,
            expires_at=expires_at,
            is_revoked=False
        )
    )
    db.commit()

    return ApiSuccess(
        message="로그인 성공",
        payload=TokenResponse(
            accessToken=access_token,
            refreshToken=refresh_token
        )
    )


@router.post("/reissue", response_model=ApiSuccess[TokenResponse], summary="토큰 재발급")
def reissue(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh = _get_refresh_from_request(request)
    if not refresh:
        raise_unauthorized("refresh token 이 필요합니다.", "UNAUTHORIZED")

    payload = decode_token(refresh)                 # refresh token 검증
    jti = payload.get("jti")
    user_id = payload.get("sub")

    if not jti or not user_id:
        raise_unauthorized("refresh token 이 유효하지 않습니다.", "UNAUTHORIZED")

    r = get_redis()
    if r.get(f"bl:rt:{jti}") == "1":               # 로그아웃 블랙리스트 체크
        raise_unauthorized("refresh token 이 유효하지 않습니다.", "UNAUTHORIZED")

    token_row = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if not token_row or token_row.is_revoked:
        raise_unauthorized("refresh token 이 유효하지 않습니다.", "UNAUTHORIZED")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise_not_found("유저를 찾을 수 없습니다.", "USER_NOT_FOUND")
    role = user.role

    token_row.is_revoked = True                     # 기존 refresh 재사용 방지
    token_row.revoked_at = datetime.now(timezone.utc)

    new_jti = uuid.uuid4().hex                      # 새 refresh 식별자
    access_token = create_access_token(
        subject=str(user_id),
        role=role
    )
    refresh_token = create_refresh_token(
        subject=str(user_id),
        jti=new_jti
    )

    response.set_cookie(
        key="refreshToken",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=False,  # JCloud HTTPS면 True 권장
        max_age=14 * 24 * 3600,
    )

    expires_at = datetime.now(timezone.utc) + timedelta(days=14)
    db.add(
        RefreshToken(                              # 새 refresh token 저장
            user_id=int(user_id),
            jti=new_jti,
            expires_at=expires_at,
            is_revoked=False
        )
    )

    db.commit()

    return ApiSuccess(
        message="토큰 재발급 성공",
        payload=TokenResponse(
            accessToken=access_token,
            refreshToken=refresh_token
        )
    )


@router.post("/logout", response_model=ApiSuccess[dict], summary="로그아웃")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh = _get_refresh_from_request(request)
    if not refresh:
        raise_bad_request("refresh token 이 필요합니다.", "BAD_REQUEST")

    payload = decode_token(refresh)
    jti = payload.get("jti")
    if not jti:
        raise_unauthorized("refresh token 이 유효하지 않습니다.", "UNAUTHORIZED")

    exp = payload.get("exp")                        # refresh 만료시간(초)
    if exp:
        now_ts = int(datetime.now(timezone.utc).timestamp())
        ttl = int(exp) - now_ts
        if ttl > 0:
            r = get_redis()
            r.setex(f"bl:rt:{jti}", ttl, "1")       # logout한 refresh는 재사용 차단

    token_row = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if token_row:
        token_row.is_revoked = True                 # refresh 즉시 폐기
        token_row.revoked_at = datetime.now(timezone.utc)
        db.commit()

    response.delete_cookie("refreshToken")
    return ApiSuccess(message="로그아웃 성공", payload={"revoked": True})