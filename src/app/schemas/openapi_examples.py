"""
Swagger(OpenAPI)
문서에 표시할 공통 예시/에러 응답 정의.
router에서 `responses=COMMON_ERROR_RESPONSES`로 재사용
엔드포인트별로 필요하면 추가/override 가능
"""

from __future__ import annotations

from app.schemas.response import ApiError

# 공통 에러 응답 예시 (400/401/403/404/422/500)
COMMON_ERROR_RESPONSES = {
    400: {
        "model": ApiError,
        "description": "Bad Request / Validation Failed",
        "content": {
            "application/json": {
                "example": {
                    "timestamp": "2025-03-05T12:34:56Z",
                    "path": "/api/example",
                    "status": 400,
                    "code": "BAD_REQUEST",
                    "message": "요청 형식이 올바르지 않습니다.",
                    "details": {"field": "reason"},
                }
            }
        },
    },
    401: {
        "model": ApiError,
        "description": "Unauthorized / Token Expired",
        "content": {
            "application/json": {
                "example": {
                    "timestamp": "2025-03-05T12:34:56Z",
                    "path": "/api/example",
                    "status": 401,
                    "code": "UNAUTHORIZED",
                    "message": "인증 토큰이 없거나 잘못된 토큰입니다.",
                    "details": None,
                }
            }
        },
    },
    403: {
        "model": ApiError,
        "description": "Forbidden (Role mismatch)",
        "content": {
            "application/json": {
                "example": {
                    "timestamp": "2025-03-05T12:34:56Z",
                    "path": "/api/example",
                    "status": 403,
                    "code": "FORBIDDEN",
                    "message": "접근 권한이 없습니다.",
                    "details": {"requiredRole": "ROLE_ADMIN"},
                }
            }
        },
    },
    404: {
        "model": ApiError,
        "description": "Resource Not Found",
        "content": {
            "application/json": {
                "example": {
                    "timestamp": "2025-03-05T12:34:56Z",
                    "path": "/api/example/999",
                    "status": 404,
                    "code": "RESOURCE_NOT_FOUND",
                    "message": "요청한 리소스를 찾을 수 없습니다.",
                    "details": {"id": 999},
                }
            }
        },
    },
    422: {
        "model": ApiError,
        "description": "Unprocessable Entity",
        "content": {
            "application/json": {
                "example": {
                    "timestamp": "2025-03-05T12:34:56Z",
                    "path": "/api/example",
                    "status": 422,
                    "code": "UNPROCESSABLE_ENTITY",
                    "message": "처리할 수 없는 요청입니다.",
                    "details": {"reason": "logical error"},
                }
            }
        },
    },
    500: {
        "model": ApiError,
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "example": {
                    "timestamp": "2025-03-05T12:34:56Z",
                    "path": "/api/example",
                    "status": 500,
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "서버 내부 오류가 발생했습니다.",
                    "details": None,
                }
            }
        },
    },
}
