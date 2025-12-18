"""
SQLAlchemy DB 세션 설정
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import get_settings

settings = get_settings()

DATABASE_URL = (
    f"mysql+pymysql://{settings.db_user}:{settings.db_password}"
    f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
)

# DB 엔진 설정
engine = create_engine(DATABASE_URL, pool_pre_ping=True) #DB 연결 끊겼는지 미리 체크하기

#세션 팩토리
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    DB 세션 의존성 요청마다 세션 열고 끝나면 닫아줌
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()