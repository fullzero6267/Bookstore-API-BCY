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

from fastapi import APIRouter, Depends, Request
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


def _get_refresh_from_request(request: Request) -> str | None:
    # 과제 구현: refresh token은 쿠키로만 받음
    return request.cookies.get("refreshToken") or request.cookies.get("refresh_token")


@router.post("/login", response_model=ApiSuccess[TokenResponse], summary="로그인")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise_not_found("유저를 찾을 수 없습니다.", "USER_NOT_FOUND")

    if not verify_password(payload.password, user.password_hash):
        raise_unauthorized("이메일 또는 비밀번호가 올바르지 않습니다.", "INVALID_CREDENTIALS")

    if hasattr(user, "is_active") and not user.is_active:
        raise_unauthorized("비활성화된 계정입니다.", "USER_INACTIVE")

    access_token = create_access_token(            # access token 발급
        sub=str(user.id),
        role=user.role
    )

    jti = uuid.uuid4().hex                          # refresh token 식별자
    refresh_token = create_refresh_token(
        sub=str(user.id),
        role=user.role,
        jti=jti
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
def reissue(request: Request, db: Session = Depends(get_db)):
    refresh = _get_refresh_from_request(request)
    if not refresh:
        raise_unauthorized("refresh token 이 필요합니다.", "UNAUTHORIZED")

    payload = decode_token(refresh)                 # refresh token 검증
    jti = payload.get("jti")
    user_id = payload.get("sub")
    role = payload.get("role", "ROLE_USER")

    if not jti or not user_id:
        raise_unauthorized("refresh token 이 유효하지 않습니다.", "UNAUTHORIZED")

    token_row = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if not token_row or token_row.is_revoked:
        raise_unauthorized("refresh token 이 유효하지 않습니다.", "UNAUTHORIZED")

    token_row.is_revoked = True                     # 기존 refresh 재사용 방지
    token_row.revoked_at = datetime.now(timezone.utc)

    new_jti = uuid.uuid4().hex                      # 새 refresh 식별자
    access_token = create_access_token(
        sub=str(user_id),
        role=role
    )
    refresh_token = create_refresh_token(
        sub=str(user_id),
        role=role,
        jti=new_jti
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
def logout(request: Request, db: Session = Depends(get_db)):
    refresh = _get_refresh_from_request(request)
    if not refresh:
        raise_bad_request("refresh token 이 필요합니다.", "BAD_REQUEST")

    payload = decode_token(refresh)
    jti = payload.get("jti")
    if not jti:
        raise_unauthorized("refresh token 이 유효하지 않습니다.", "UNAUTHORIZED")

    token_row = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if token_row:
        token_row.is_revoked = True                 # refresh 즉시 폐기
        token_row.revoked_at = datetime.now(timezone.utc)
        db.commit()

    return ApiSuccess(message="로그아웃 성공", payload={"revoked": True})