from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.config import get_settings
import uuid

settings = get_settings()


def _now_utc() -> datetime:  # JWT 표준에 맞춘 UTC 현재 시간
    return datetime.now(timezone.utc)


def create_access_token(subject: str, role: str) -> str:  # access token 발급
    expire = _now_utc() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "type": "access",        # 토큰 타입 구분
        "sub": subject,          # user_id (문자열)
        "role": role,            # 권한 정보
        "exp": expire,           # 만료 시간
        "iat": _now_utc(),       # 발급 시간
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> tuple[str, str, datetime]:  # refresh token + jti 생성
    expire = _now_utc() + timedelta(days=settings.jwt_refresh_token_expire_days)
    jti = str(uuid.uuid4())      # 서버에서 관리할 refresh 식별자
    payload = {
        "type": "refresh",      # refresh token 구분
        "sub": subject,         # user_id
        "jti": jti,             # DB 저장용 토큰 ID
        "exp": expire,
        "iat": _now_utc(),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, jti, expire    # (토큰, 식별자, 만료 시각)