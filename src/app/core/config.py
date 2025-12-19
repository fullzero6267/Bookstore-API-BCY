from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):  # 환경변수(.env) 설정을 한 곳에서 관리함
    app_name: str = "Bookstore"
    app_version: str = "1.0.0"

    app_host: str = "0.0.0.0"
    app_port: int = 8080

    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    cors_origins: str = ""

    class Config:  # .env 파일 로드 세팅
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def database_url(self) -> str:  # DB 접속용 URL 생성
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:  # Settings 객체를 싱글톤처럼 재사용
    return Settings()