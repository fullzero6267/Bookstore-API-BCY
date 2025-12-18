"""
책
Books API
목록(공개/일반), 상세, ADMIN CRUD
목록 공통 규격: page/size/sort/keyword/category
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_roles                 # ADMIN 권한 체크
from app.core.errors import raise_not_found            # 404 공통 예외
from app.core.pagenation import paginate               # 공통 페이지네이션 유틸
from app.core.query_utils import (
    apply_keyword_filter,                              # title/author 검색
    apply_sort,                                        # sort 파라미터 화이트리스트
    apply_exact_filter,                                # category 같은 exact 필터
)
from app.db.session import get_db                      # DB 세션 주입
from app.models.book import Book
from app.models.user import User
from app.schemas.book import BookCreate, BookUpdate, BookResponse
from app.schemas.response import ApiSuccess             # 공통 성공 응답 포맷
from app.schemas.openapi_examples import COMMON_ERROR_RESPONSES

router = APIRouter(tags=["Books"], responses=COMMON_ERROR_RESPONSES)  # api prefix는 main에서 붙음


def _list_books(
    db: Session,
    page: int,
    size: int,
    sort: str,
    keyword: str | None,
    category: str | None,
):
    q = db.query(Book)                                  # 목록 기본 쿼리
    q = apply_exact_filter(q, Book, "category", category) # category 필터
    q = apply_keyword_filter(q, Book, keyword, fields=["title", "author"])  # keyword 검색
    q = apply_sort(                                     # 정렬: 허용된 필드만
        q,
        sort,
        allowed={
            "created_at": Book.created_at,
            "price": Book.price,
            "title": Book.title,
            "stock": Book.stock,
        },
        default="created_at,DESC",
    )

    page_dict = paginate(q, page=page, size=size, sort=sort)  # page/size 적용
    page_dict["content"] = [BookResponse.model_validate(x) for x in page_dict["content"]]  # 응답 DTO 변환
    return page_dict


@router.get(
    "/public/books",
    response_model=ApiSuccess[dict],
    summary="공개 도서 목록 조회",
)
def 공개_도서_목록(
    page: int = Query(0, ge=0, description="0부터 시작"),
    size: int = Query(20, ge=1, le=100, description="기본 20, 최대 100"),
    sort: str = Query("created_at,DESC", description="예: created_at,DESC / price,ASC / title,ASC"),
    keyword: str | None = Query(None, description="title/author 부분일치 검색"),
    category: str | None = Query(None, description="카테고리 필터"),
    db: Session = Depends(get_db),
):
    # 공개 엔드포인트(로그인 없이 목록 확인)
    return ApiSuccess(message="도서 목록 조회 성공", payload=_list_books(db, page, size, sort, keyword, category))


@router.get(
    "/books",
    response_model=ApiSuccess[dict],
    summary="도서 목록 조회",
)
def 도서_목록(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    sort: str = Query("created_at,DESC"),
    keyword: str | None = Query(None),
    category: str | None = Query(None),
    db: Session = Depends(get_db),
):
    # 과제 요구: /books도 공개와 동일 규격(인증 없이 가능)
    return ApiSuccess(message="도서 목록 조회 성공", payload=_list_books(db, page, size, sort, keyword, category))


@router.get(
    "/books/{bookId}",
    response_model=ApiSuccess[BookResponse],
    summary="도서 상세 조회",
)
def 도서_상세(bookId: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.id == bookId).first()  # 상세 조회
    if not book:
        raise_not_found("도서를 찾을 수 없습니다.", "RESOURCE_NOT_FOUND")
    return ApiSuccess(message="도서 상세 조회 성공", payload=book)  # response_model이 BookResponse라 그대로 가능


@router.post(
    "/books",
    response_model=ApiSuccess[BookResponse],
    summary="(ADMIN) 도서 등록",
)
def 도서_등록(
    body: BookCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("ROLE_ADMIN")),  # 관리자만 등록 가능
):
    book = Book(                                           # 요청 DTO  모델 변환
        title=body.title,
        author=body.author,
        category=body.category,
        description=body.description,
        price=body.price,
        stock=body.stock,
    )
    db.add(book)
    db.commit()
    db.refresh(book)                                       # 생성된 id 등 반영
    return ApiSuccess(message="도서 등록 성공", payload=book)


@router.patch(
    "/books/{bookId}",
    response_model=ApiSuccess[BookResponse],
    summary="(ADMIN) 도서 수정",
)
def 도서_수정(
    bookId: int,
    body: BookUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("ROLE_ADMIN")),   # 관리자만 수정 가능
):
    book = db.query(Book).filter(Book.id == bookId).first()
    if not book:
        raise_not_found("도서를 찾을 수 없습니다.", "RESOURCE_NOT_FOUND")

    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(book, k, v)                                # PATCH: 들어온 필드만 업데이트

    db.commit()
    db.refresh(book)
    return ApiSuccess(message="도서 수정 성공", payload=book)


@router.delete(
    "/books/{bookId}",
    response_model=ApiSuccess[dict],
    summary="(ADMIN) 도서 삭제",
)
def 도서_삭제(
    bookId: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("ROLE_ADMIN")),   # 관리자만 삭제 가능
):
    book = db.query(Book).filter(Book.id == bookId).first()
    if not book:
        raise_not_found("도서를 찾을 수 없습니다.", "RESOURCE_NOT_FOUND")

    db.delete(book)                                        # 하드 삭제
    db.commit()
    return ApiSuccess(message="도서 삭제 성공", payload={"deleted": True})