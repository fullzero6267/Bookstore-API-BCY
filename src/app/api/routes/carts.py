"""
카드
Cart API
로그인 사용자 기준 장바구니 CRUD
DB 연동 버전
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user          # 로그인 사용자 주입
from app.core.errors import raise_not_found, raise_bad_request
from app.db.session import get_db                  # DB 세션
from app.models.book import Book
from app.models.cart_item import CartItem          # 장바구니 아이템 모델
from app.models.user import User
from app.schemas.cart import (
    CartItemCreate,
    CartItemUpdate,
    CartItemResponse,
)
from app.schemas.response import ApiSuccess         # 공통 성공 응답
from app.schemas.openapi_examples import COMMON_ERROR_RESPONSES


router = APIRouter(
    responses=COMMON_ERROR_RESPONSES               # 공통 에러 응답
)


@router.get(
    "/items",
    response_model=ApiSuccess[list[CartItemResponse]],
    summary="장바구니 아이템 조회",
)
def 장바구니_아이템_조회(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user), # 본인 장바구니만 조회
):
    items = (
        db.query(CartItem)
        .filter(CartItem.user_id == current_user.id) # 사용자 기준 필터
        .order_by(CartItem.id.desc())
        .all()
    )
    return ApiSuccess(message="장바구니 조회 성공", payload=items)


@router.post(
    "/items",
    response_model=ApiSuccess[CartItemResponse],
    summary="장바구니 담기",
)
def 장바구니_담기(
    body: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user), # 로그인 필수
):
    book = db.query(Book).filter(Book.id == body.book_id).first()
    if not book:
        raise_not_found("도서를 찾을 수 없습니다.", "RESOURCE_NOT_FOUND")

    if body.quantity <= 0:
        raise_bad_request(                          # 수량 최소값 검증
            "수량은 1 이상이어야 합니다.",
            "VALIDATION_FAILED",
            details={"quantity": "must be >= 1"},
        )

    # 이미 담긴 도서면 수량 누적, 없으면 새로 생성
    item = (
        db.query(CartItem)
        .filter(
            CartItem.user_id == current_user.id,
            CartItem.book_id == body.book_id,
        )
        .first()
    )

    if item:
        item.quantity += body.quantity               # 기존 수량 증가
    else:
        item = CartItem(
            user_id=current_user.id,
            book_id=body.book_id,
            quantity=body.quantity,
        )
        db.add(item)

    db.commit()
    db.refresh(item)
    return ApiSuccess(message="장바구니 담기 성공", payload=item)


@router.patch(
    "/items/{itemId}",
    response_model=ApiSuccess[CartItemResponse],
    summary="장바구니 수량 변경",
)
def 장바구니_수량_변경(
    itemId: int,
    body: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = (
        db.query(CartItem)
        .filter(
            CartItem.id == itemId,
            CartItem.user_id == current_user.id,    # 본인 아이템만 수정 가능
        )
        .first()
    )
    if not item:
        raise_not_found("장바구니 아이템을 찾을 수 없습니다.", "RESOURCE_NOT_FOUND")

    if body.quantity <= 0:
        raise_bad_request(
            "수량은 1 이상이어야 합니다.",
            "VALIDATION_FAILED",
            details={"quantity": "must be >= 1"},
        )

    item.quantity = body.quantity                    # 수량 직접 변경
    db.commit()
    db.refresh(item)
    return ApiSuccess(message="장바구니 수량 변경 성공", payload=item)


@router.delete(
    "/items/{itemId}",
    response_model=ApiSuccess[dict],
    summary="장바구니 아이템 삭제",
)
def 장바구니_아이템_삭제(
    itemId: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = (
        db.query(CartItem)
        .filter(
            CartItem.id == itemId,
            CartItem.user_id == current_user.id,    # 본인 아이템만 삭제
        )
        .first()
    )
    if not item:
        raise_not_found("장바구니 아이템을 찾을 수 없습니다.", "RESOURCE_NOT_FOUND")

    db.delete(item)
    db.commit()
    return ApiSuccess(message="장바구니 아이템 삭제 성공", payload={"deleted": True})


@router.delete(
    "/clear",
    response_model=ApiSuccess[dict],
    summary="장바구니 비우기",
)
def 장바구니_비우기(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 사용자 장바구니 전체 삭제
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    db.commit()
    return ApiSuccess(message="장바구니 비우기 성공", payload={"cleared": True})