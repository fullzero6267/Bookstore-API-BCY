"""
Redis 연결
로그아웃 블랙리스트 / rate-limit 같은 전역 기능에 사용가능
"""

from __future__ import annotations

from redis import Redis
from app.core.config import get_settings

_redis: Redis | None = None


def get_redis() -> Redis:
    # redis client는 싱글톤처럼 재사용
    global _redis
    if _redis is None:
        settings = get_settings()
        _redis = Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True,  # 문자열로 바로 받기
        )
    return _redis