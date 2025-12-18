"""
과제용 공통 예외,에러 유틸.
모든 에러는 ApiException으로 올리고(main.py 핸들러에서 표준 포맷으로 응답
라우터,서비스에서 쉽게 가능하도록 raise helper를 제공
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

from app.core.error_code import ErrorCode


@dataclass
class ApiException(Exception):
    status: int
    # 문자열도 허용. 신규 코드는 ErrorCode 사용.
    code: Union[ErrorCode, str]
    message: str
    details: Optional[dict] = None



# Raise

def _raise(status: int, message: str, code: Union[ErrorCode, str], details: Optional[dict] = None) -> None:
    """ApiException을 발생시키는 내부 유틸"""
    raise ApiException(status=status, code=code, message=message, details=details)


def raise_bad_request(message: str = "잘못된 요청입니다.", code: Union[ErrorCode, str] = ErrorCode.BAD_REQUEST, details: Optional[dict] = None) -> None:
    _raise(400, message, code, details)


def raise_unauthorized(message: str = "인증이 필요합니다.", code: Union[ErrorCode, str] = ErrorCode.UNAUTHORIZED, details: Optional[dict] = None) -> None:
    _raise(401, message, code, details)


def raise_forbidden(message: str = "접근 권한이 없습니다.", code: Union[ErrorCode, str] = ErrorCode.FORBIDDEN, details: Optional[dict] = None) -> None:
    _raise(403, message, code, details)


def raise_not_found(message: str = "리소스를 찾을 수 없습니다.", code: Union[ErrorCode, str] = ErrorCode.RESOURCE_NOT_FOUND, details: Optional[dict] = None) -> None:
    _raise(404, message, code, details)


def raise_conflict(message: str = "리소스 충돌이 발생했습니다.", code: Union[ErrorCode, str] = ErrorCode.DUPLICATE_RESOURCE, details: Optional[dict] = None) -> None:
    _raise(409, message, code, details)


def raise_unprocessable(message: str = "처리할 수 없는 요청입니다.", code: Union[ErrorCode, str] = ErrorCode.UNPROCESSABLE_ENTITY, details: Optional[dict] = None) -> None:
    _raise(422, message, code, details)
