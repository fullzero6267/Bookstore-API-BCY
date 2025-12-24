"""
app.main
에러 응답 포맷 한 곳에서 통일
/health 는 인증 없이 열어둠(배포 확인하는용)
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse


from app.api.routes import auth, users, books, carts, orders, favorites, reviews, admin
from app.core.error_code import ErrorCode
from app.core.errors import ApiException
from app.schemas.response import now_utc_iso


def redis_storage_uri() -> str:
    host = os.getenv("REDIS_HOST", "redis")
    port = os.getenv("REDIS_PORT", "6379")
    db = os.getenv("REDIS_DB", "0")
    return f"redis://{host}:{port}/{db}"


limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=redis_storage_uri(),
)


app = FastAPI(title="Bookstore API")
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


def _error_payload(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: dict | None = None,
):
    return {
        "timestamp": now_utc_iso(),
        "path": request.url.path,
        "status": status_code,
        "code": code,
        "message": message,
        "details": details,
    }


@app.exception_handler(RateLimitExceeded)
async def ratelimit_exception_handler(request: Request, exc: RateLimitExceeded):
    # 429도 너희 표준 포맷으로 고정
    return JSONResponse(
        status_code=429,
        content=_error_payload(
            request,
            429,
            ErrorCode.TOO_MANY_REQUESTS,
            "요청이 너무 많습니다. 잠시 후 다시 시도해주세요.",
        ),
    )


@app.middleware("http")
async def log_request(request: Request, call_next):
    start = time.perf_counter()
    try:
        return await call_next(request)
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"[REQ] {request.method} {request.url.path} ({elapsed_ms:.1f}ms)")


@app.exception_handler(ApiException)
async def api_exception_handler(request: Request, exc: ApiException):
    return JSONResponse(
        status_code=exc.status,
        content=_error_payload(request, exc.status, exc.code, exc.message, exc.details),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
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
        code = ErrorCode.BAD_REQUEST

    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(request, exc.status_code, code, str(exc.detail)),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    import traceback

    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content=_error_payload(
            request, 500, ErrorCode.INTERNAL_SERVER_ERROR, "서버 내부 오류가 발생했습니다."
        ),
    )


@app.get("/health", summary="헬스체크", tags=["Health"])
@limiter.limit("30/minute")  # Redis를 확실히 쓰는 지점
def health(request: Request):
    return {
        "status": "ok",
        "version": "0.1.0",
        "buildTime": datetime.now(timezone.utc).isoformat(),
    }


# 라우터 등록
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(users.router, prefix="/api", tags=["Users"])
app.include_router(books.router, prefix="/api", tags=["Books"])
app.include_router(carts.router, prefix="/api", tags=["Carts"])
app.include_router(orders.router, prefix="/api", tags=["Orders"])
app.include_router(favorites.router, prefix="/api", tags=["Favorites"])
app.include_router(reviews.router, prefix="/api", tags=["Reviews"])
app.include_router(admin.router, prefix="/api", tags=["Admin"])