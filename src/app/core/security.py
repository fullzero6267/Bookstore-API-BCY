"""
비밀번호 관련 보안
평문 비밀번호를 DB에 저장하면 안 됨
bcrypt로 해시해서 저장
"""
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from app.core.config import get_settings
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError
from fastapi import HTTPException, status
from app.core.errors import raise_unauthorized

settings = get_settings()
# 어떤 해시 알고리즘을 쓸지 설정
# bcrypt 많이 쓰임
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)
# 평문 비밀번호 해시된 문자열로 변환
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# 로그인 시 입력한 비밀번호와 DB에 저장된 해시를 비교
def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def create_access_token(subject: str, role: str | None = None) -> str:

    #subject: user_id 또는 email (user_id를 문자열로)

    settings = get_settings()
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    payload = {
        "sub": subject,
        "type": "access",
        "role": role, # RBAC 편의를 위해 role도 access 토큰에 포함(최종 권한 판단은 DB의 user.role 기준으로도 가능함)
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_access_token(token: str) -> dict:

    # Access Token 디코딩, 검증
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )

        # 토큰 타입확인 (access 전용)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="INVALID_TOKEN_TYPE",
            )

        return payload

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_OR_EXPIRED_TOKEN",
        )

def create_refresh_token(subject: str, jti: str) -> str:
    """
    refresh 토큰은 토큰 고유값(jti) 넣어서 DB랑 매칭
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=settings.jwt_refresh_token_expire_days)

    payload = {
        "sub": subject,
        "type": "refresh",
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_token(token: str) -> dict:

    #JWT 토큰 디코딩,서명 검증,exp 검증
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except ExpiredSignatureError:
        # exp 만료
        raise_unauthorized("토큰이 만료되었습니다.", "TOKEN_EXPIRED")
    except JWTError:
        # 서명 위조/형식 오류 등
        raise_unauthorized("유효하지 않은 토큰입니다.", "UNAUTHORIZED")