"""
의존성
get_current_user access token 검증 → User 반환
require_roles RBAC 권한 체크
"""

from __future__ import annotations

from typing import Callable, Optional

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.core.security import decode_token
from app.core.errors import raise_unauthorized, raise_forbidden

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    auto_error=False,  # 토큰 없을 때 직접 처리
)


def _extract_access_token(  # 헤더/쿠키에서 access token 추출
    request: Request,
    bearer: Optional[str],
) -> Optional[str]:
    if bearer:  # Authorization: Bearer <token>
        return bearer
    return request.cookies.get("accessToken") or request.cookies.get("access_token")


def get_current_user(  # access token 검증 후 user 반환
    request: Request,
    db: Session = Depends(get_db),
    bearer: Optional[str] = Depends(oauth2_scheme),
) -> User:
    token = _extract_access_token(request, bearer)
    if not token:
        raise_unauthorized("인증 토큰이 필요합니다.", "UNAUTHORIZED")

    payload = decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise_unauthorized("유효하지 않은 토큰입니다.", "UNAUTHORIZED")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise_unauthorized("유효하지 않은 토큰입니다.", "UNAUTHORIZED")

    if hasattr(user, "is_active") and not user.is_active:
        raise_unauthorized("비활성화된 계정입니다.", "USER_INACTIVE")

    return user


def require_roles(*roles: str) -> Callable[[User], User]:  # 특정 role만 허용하는 의존성 생성기
    def _dep(  # 인증 + 권한 체크
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in roles:
            raise_forbidden("접근 권한이 없습니다.", "FORBIDDEN")
        return current_user

    return _dep