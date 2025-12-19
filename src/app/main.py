"""
app.main
에러 응답 포맷 한 곳에서 통일
/health 는 인증 없이 열어둠(배포 확인하는용)
"""

from __future__ import annotations
import time
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from app.api.routes import auth, users, books, carts, orders, favorites, reviews, admin
from app.core.error_code import ErrorCode
from app.core.errors import ApiException
from app.schemas.response import now_utc_iso

app = FastAPI(title="Bookstore API")


@app.middleware("http")  # 요청 시간만 간단히 로깅(민감정보는 안 찍음)
async def log_request(request: Request, call_next):
    start = time.perf_counter()
    try:
        return await call_next(request)
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"[REQ] {request.method} {request.url.path} ({elapsed_ms:.1f}ms)")


def _error_payload(request: Request, status_code: int, code: str, message: str, details: dict | None = None):
    # 표준 에러 포맷 여기서 shape 고정
    return {
        "timestamp": now_utc_iso(),   # UTC ISO 통일
        "path": request.url.path,
        "status": status_code,
        "code": code,                # 내부 에러코드(문서 테스트용)
        "message": message,
        "details": details,          # 필요할 때만 채움
    }


@app.exception_handler(ApiException)
async def api_exception_handler(request: Request, exc: ApiException):
    # 서비스 레벨에서 의도적으로 던진 예외는 그대로 표준 포맷으로
    return JSONResponse(
        status_code=exc.status,
        content=_error_payload(request, exc.status, exc.code, exc.message, exc.details),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # 입력 검증 실패 = 어떤 필드가 깨졌는지 errors()만 내려줌
    return JSONResponse(
        status_code=422,
        content=_error_payload(
            request,
            422,
            ErrorCode.VALIDATION_FAILED,
            "입력 값 검증에 실패했습니다.",
            {"errors": exc.errors()},
        ),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # FastAPI 기본 HTTPException 에러코드로만 매핑해서 통일
    if exc.status_code == 400:
        code = ErrorCode.BAD_REQUEST
    elif exc.status_code == 401:
        code = ErrorCode.UNAUTHORIZED
    elif exc.status_code == 403:
        code = ErrorCode.FORBIDDEN
    elif exc.status_code == 404:
        code = ErrorCode.RESOURCE_NOT_FOUND
    elif exc.status_code == 409:
        code = ErrorCode.STATE_CONFLICT
    elif exc.status_code == 422:
        code = ErrorCode.UNPROCESSABLE_ENTITY
    elif exc.status_code == 429:
        code = ErrorCode.TOO_MANY_REQUESTS
    else:
        code = ErrorCode.BAD_REQUEST  # 애매한 건 일단 400 계열로 묶음

    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(request, exc.status_code, code, str(exc.detail)),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # 예상 못한 예외는 500으로 통일(로그만)
    import traceback
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content=_error_payload(request, 500, ErrorCode.INTERNAL_SERVER_ERROR, "서버 내부 오류가 발생했습니다."),
    )


@app.get("/health", summary="헬스체크", tags=["Health"])
def health():
    #  배포 체크용 인증 없이 ok만
    return {
        "status": "ok",
        "version": "0.1.0",
        "buildTime": datetime.now(timezone.utc).isoformat(),
    }


# 라우터는 여기서 한 번에 등록(경로 규칙 통일 + Swagger)
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(users.router, prefix="/api", tags=["Users"])
app.include_router(books.router, prefix="/api", tags=["Books"])
app.include_router(carts.router, prefix="/api", tags=["Carts"])
app.include_router(orders.router, prefix="/api", tags=["Orders"])
app.include_router(favorites.router, prefix="/api", tags=["Favorites"])
app.include_router(reviews.router, prefix="/api", tags=["Reviews"])
app.include_router(admin.router, prefix="/api", tags=["Admin"])