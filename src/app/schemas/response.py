"""
과제용 공통 응답 스키마
성공, 실패, 페이지네이션 응답
"""

from __future__ import annotations

from datetime import datetime
from typing import Generic, Optional, TypeVar, List

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

T = TypeVar("T")


def now_utc_iso() -> str:  # UTC 기준 ISO 포맷 시간 문자열 생성
    return datetime.utcnow().isoformat() + "Z"


class ApiSuccess(GenericModel, Generic[T]):  # 공통 성공 응답 래퍼
    isSuccess: bool = Field(default=True)
    message: str = Field(...)
    payload: Optional[T] = Field(default=None)


class ApiError(BaseModel):  # 공통 에러 응답 포맷
    timestamp: str
    path: str
    status: int
    code: str
    message: str
    details: Optional[dict] = None


U = TypeVar("U")


class PageResponse(GenericModel, Generic[U]):  # 페이지네이션 응답 DTO
    content: List[U]
    page: int
    size: int
    totalElements: int
    totalPages: int
    sort: str = ""