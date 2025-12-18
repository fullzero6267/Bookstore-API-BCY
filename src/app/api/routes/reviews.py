"""
Reviews API
- 도서별 리뷰, 내 리뷰, 리뷰 수정·삭제
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user          # 로그인 사용자 주입
from app.core.errors import raise_forbidden, raise_not_found
from app.db.session import get_db                  # DB 세션
from app.models.book import Book
from app.models.review import Review               # 리뷰 모델
from app.models.user import User
from app.schemas.response import ApiSuccess        # 공통 성공 응답
from app.schemas.openapi_examples import COMMON_ERROR_RESPONSES
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewResponse

router = APIRouter(responses=COMMON_ERROR_RESPONSES)  # /api prefix는 main에서


@router.get(
    "/books/{bookId}/reviews",
    response_model=ApiSuccess[list[ReviewResponse]],
    summary="도서 리뷰 목록 조회",
)
def 도서_리뷰_목록_조회(
    bookId: int,
    db: Session = Depends(get_db),
):
    book = db.query(Book).filter(Book.id == bookId).first()  # 존재 확인
    if not book:
        raise_not_found("도서를 찾을 수 없습니다.", "RESOURCE_NOT_FOUND")

    reviews = (
        db.query(Review)
        .filter(Review.book_id == bookId)                    # 도서 기준 조회
        .order_by(Review.id.desc())
        .all()
    )
    return ApiSuccess(message="리뷰 목록 조회 성공", payload=reviews)


@router.post(
    "/books/{bookId}/reviews",
    response_model=ApiSuccess[ReviewResponse],
    summary="도서 리뷰 작성",
)
def 도서_리뷰_작성(
    bookId: int,
    body: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),          # 로그인 필요
):
    book = db.query(Book).filter(Book.id == bookId).first()
    if not book:
        raise_not_found("도서를 찾을 수 없습니다.", "RESOURCE_NOT_FOUND")

    review = Review(
        user_id=current_user.id,                             # 작성자
        book_id=bookId,
        rating=body.rating,
        content=body.content,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return ApiSuccess(message="리뷰 작성 성공", payload=review)


@router.get(
    "/reviews/me",
    response_model=ApiSuccess[list[ReviewResponse]],
    summary="내 리뷰 조회",
)
def 내_리뷰_조회(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reviews = (
        db.query(Review)
        .filter(Review.user_id == current_user.id)           # 내 리뷰만
        .order_by(Review.id.desc())
        .all()
    )
    return ApiSuccess(message="내 리뷰 조회 성공", payload=reviews)


@router.patch(
    "/reviews/{reviewId}",
    response_model=ApiSuccess[ReviewResponse],
    summary="리뷰 수정",
)
def 리뷰_수정(
    reviewId: int,
    body: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = db.query(Review).filter(Review.id == reviewId).first()
    if not review:
        raise_not_found("리뷰를 찾을 수 없습니다.", "RESOURCE_NOT_FOUND")

    if review.user_id != current_user.id:
        raise_forbidden("본인 리뷰만 수정할 수 있습니다.", "FORBIDDEN")  # 권한 체크

    if body.rating is not None:
        review.rating = body.rating
    if body.content is not None:
        review.content = body.content

    db.commit()
    db.refresh(review)
    return ApiSuccess(message="리뷰 수정 성공", payload=review)


@router.delete(
    "/reviews/{reviewId}",
    response_model=ApiSuccess[dict],
    summary="리뷰 삭제",
)
def 리뷰_삭제(
    reviewId: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = db.query(Review).filter(Review.id == reviewId).first()
    if not review:
        raise_not_found("리뷰를 찾을 수 없습니다.", "RESOURCE_NOT_FOUND")

    if review.user_id != current_user.id:
        raise_forbidden("본인 리뷰만 삭제할 수 있습니다.", "FORBIDDEN")  # 권한 체크

    db.delete(review)
    db.commit()
    return ApiSuccess(message="리뷰 삭제 성공", payload={"deleted": True})