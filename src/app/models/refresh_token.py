"""
Refresh Token을 DB에 저장해 로그아웃/재발급 시 revoke 할 수 있게 한다.
토큰 문자열 자체는 저장하지 않고(jti만 저장)
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.db.base import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 토큰 자체를 저장하지 않고(유출 위험), jti만 저장해서 “유효 토큰인지” 체크
    jti = Column(String(64), unique=True, nullable=False, index=True)

    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_revoked = Column(Boolean, nullable=False, default=False)