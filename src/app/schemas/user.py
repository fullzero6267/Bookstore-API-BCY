"""
User 관련 Pydantic 스키마
API 요청/응답의 형태를 정의
입력 검증 자동 처리
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"email": "user1@example.com", "password": "P@ssw0rd!", "name": "홍길동"}]})
    # 회원가입 요청용 스키마
    email: EmailStr                 # 이메일 형식 검증 자동
    password: str = Field(min_length=8, max_length=60)   # bcrypt 권장 길이 72
    name: str = Field(min_length=1, max_length=100)


class UserResponse(BaseModel):

    # 회원가입,조회 응답용 스키마 (비밀번호는 포함 x)
    id: int
    email: EmailStr
    name: str
    role: str
    is_active: bool

    class Config:
        # SQLAlchemy 모델을 그대로 반환 가능하게 해줌
        from_attributes = True

class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    password: str | None = Field(default=None, min_length=8, max_length=60)
