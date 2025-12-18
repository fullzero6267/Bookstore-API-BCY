"""
amin router
관리자 전용 API
사용자 관리
간단 통계 조회
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_roles          # 관리자 권한 체크용 의존성
from app.core.pagenation import paginate        # 공통 페이지네이션 유틸
from app.core.query_utils import (
    apply_keyword_filter,                       # 키워드 검색(email/name)
    apply_sort,                                 # 정렬 파라미터 처리
    apply_exact_filter                          # 정확 일치 필터(role)
)
from app.core.errors import raise_not_found     # 404 공통 예외
from app.db.session import get_db               # DB 세션 주입
from app.models.user import User
from app.models.book import Book
from app.models.order import Order
from app.schemas.user import UserResponse       # 사용자 응답 DTO
from app.schemas.response import ApiSuccess     # 공통 성공 응답 포맷
from app.schemas.openapi_examples import COMMON_ERROR_RESPONSES

router = APIRouter(
    prefix="/admin",                            # 관리자 API prefix
    tags=["Admin"],
    responses=COMMON_ERROR_RESPONSES            # 공통 에러 응답 예시
)


@router.get(
    "/users",
    response_model=ApiSuccess[dict],
    summary="(ADMIN) 사용자 목록 조회",
)
def 관리자_사용자_목록(
    page: int = Query(0, ge=0),                  # 페이지 번호
    size: int = Query(20, ge=1, le=100),         # 페이지 크기 제한
    sort: str = Query("created_at,DESC"),        # 정렬 기준
    keyword: str | None = Query(None),           # email,name 검색
    role: str | None = Query(None),              # 역할 필터
    isActive: bool | None = Query(None),         # 활성 여부 필터
    db: Session = Depends(get_db),               # DB 세션
    _admin: User = Depends(require_roles("ROLE_ADMIN")),  # 관리자만 접근
):
    q = db.query(User)                           # 사용자 목록 기본 쿼리

    q = apply_keyword_filter(                    # 키워드 검색 적용
        q, User, keyword, fields=["email", "name"]
    )

    q = apply_exact_filter(q, User, "role", role)  # role 정확 필터

    if isActive is not None:
        q = q.filter(User.is_active == isActive)  # 활성 비활성 필터

    q = apply_sort(                              # 허용된 컬럼만 정렬
        q,
        sort,
        allowed={
            "created_at": User.created_at,
            "email": User.email,
            "name": User.name,
            "role": User.role,
        },
        default="created_at,DESC",
    )

    page_dict = paginate(q, page=page, size=size, sort=sort)  # 페이지네이션 적용
    page_dict["content"] = [
        UserResponse.model_validate(x)            # 응답 DTO로 변환
        for x in page_dict["content"]
    ]

    return ApiSuccess(
        message="사용자 목록 조회 성공",
        payload=page_dict
    )


@router.patch(
    "/users/{userId}/deactivate",
    response_model=ApiSuccess[dict],
    summary="(ADMIN) 사용자 비활성화",
)
def 관리자_사용자_비활성화(
    userId: int,
    db: Session = Depends(get_db),                # DB 세션
    _admin: User = Depends(require_roles("ROLE_ADMIN")),  # 관리자 권한
):
    user = db.query(User).filter(User.id == userId).first()  # 대상 사용자 조회
    if not user:
        raise_not_found("사용자를 찾을 수 없습니다.", "USER_NOT_FOUND")

    user.is_active = False                        # soft 비활성화
    db.commit()

    return ApiSuccess(
        message="사용자 비활성화 성공",
        payload={"userId": userId, "is_active": False}
    )


@router.get(
    "/stats/summary",
    response_model=ApiSuccess[dict],
    summary="(ADMIN) 간단 통계",
)
def 관리자_통계(
    db: Session = Depends(get_db),                # DB 세션
    _admin: User = Depends(require_roles("ROLE_ADMIN")),  # 관리자 전용
):
    users = db.query(User).count()                # 사용자 수
    books = db.query(Book).count()                # 도서 수
    orders = db.query(Order).count()              # 주문 수

    return ApiSuccess(
        message="통계 조회 성공",
        payload={
            "users": users,
            "books": books,
            "orders": orders,
        }
    )