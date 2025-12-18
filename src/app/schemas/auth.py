from __future__ import annotations

from pydantic import BaseModel, Field, EmailStr, ConfigDict


class LoginRequest(BaseModel):  # 로그인 요청 DTO(email/password)
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"email": "user1@example.com", "password": "P@ssw0rd!"}
            ]
        }
    )
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=200)


class TokenResponse(BaseModel):  # 로그인/재발급 응답용 토큰 묶음
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"accessToken": "eyJhbGciOi...", "refreshToken": "eyJhbGciOi..."}
            ]
        }
    )
    accessToken: str
    refreshToken: str