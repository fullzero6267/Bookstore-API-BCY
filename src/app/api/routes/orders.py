"""
Orders API (과제)
주문 생성, 내 주문 조회, 내 주문 상세, 내 주문 아이템, ADMIN 상태 변경
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_roles   # 로그인/권한 체크
from app.core.errors import raise_bad_request, raise_not_found
from app.core.pagenation import paginate                   # 공통 페이지네이션
from app.core.query_utils import apply_sort, apply_exact_filter
from app.db.session import get_db                           # DB 세션
from app.models.book import Book
from app.models.order import Order, OrderItem               # 주문/주문아이템 모델
from app.models.user import User
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderItemResponse,
    OrderStatusUpdate,
)
from app.schemas.response import ApiSuccess                 # 공통 성공 응답
from app.schemas.openapi_examples import COMMON_ERROR_RESPONSES

router = APIRouter(prefix="/orders", tags=["Orders"], responses=COMMON_ERROR_RESPONSES)


@router.post("", response_model=ApiSuccess[OrderResponse], summary="주문 생성")
def 주문_생성(
    body: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),         # 로그인 필요
):
    total = 0
    items: list[OrderItem] = []

    for it in body.items:
        book = db.query(Book).filter(Book.id == it.bookId).first()
        if not book:
            raise_not_found("도서를 찾을 수 없습니다.", "RESOURCE_NOT_FOUND")
        if book.stock < it.quantity:
            raise_bad_request("재고가 부족합니다.", "UNPROCESSABLE_ENTITY")

        book.stock -= it.quantity                            # 주문 생성 시 재고 선차감

        unit_price = int(book.price or 0)                    # 주문 당시 가격 스냅샷
        total += unit_price * it.quantity
        items.append(
            OrderItem(book_id=book.id, quantity=it.quantity, unit_price=unit_price)  # item은 나중에 order_id 연결
        )

    order = Order(user_id=current_user.id, status="CREATED", total_price=total)  # 주문 헤더 생성
    db.add(order)
    db.flush()                                           # order.id 확보용

    for oi in items:
        oi.order_id = order.id                            # order_id 연결
        db.add(oi)

    db.commit()
    db.refresh(order)

    # 응답에 items 포함하려고 주문아이템 다시 조회(응답 DTO 구성용)
    order_items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    payload = OrderResponse(
        id=order.id,
        userId=order.user_id,
        status=order.status,
        totalPrice=order.total_price,
        items=[
            OrderItemResponse(
                id=x.id,
                orderId=x.order_id,
                bookId=x.book_id,
                quantity=x.quantity,
                price=x.unit_price,
            )
            for x in order_items
        ],
    )
    return ApiSuccess(message="주문 생성 성공", payload=payload)


@router.get("", response_model=ApiSuccess[dict], summary="내 주문 목록 조회")
def 내_주문_목록(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    sort: str = Query("created_at,DESC"),
    status: str | None = Query(None, description="상태 필터(예: CREATED)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),         # 내 주문만 조회
):
    q = db.query(Order).filter(Order.user_id == current_user.id)  # 사용자 기준 필터
    q = apply_exact_filter(q, Order, "status", status)            # status 필터
    q = apply_sort(                                               # 정렬: 허용 필드만
        q,
        sort,
        allowed={
            "created_at": Order.created_at,
            "total_price": Order.total_price,
            "status": Order.status,
        },
        default="created_at,DESC",
    )
    page_dict = paginate(q, page=page, size=size, sort=sort)      # page/size 적용
    page_dict["content"] = [
        OrderResponse(id=o.id, userId=o.user_id, status=o.status, totalPrice=o.total_price, items=None)  # 목록은 items 생략
        for o in page_dict["content"]
    ]
    return ApiSuccess(message="내 주문 목록 조회 성공", payload=page_dict)


@router.get("/{orderId}", response_model=ApiSuccess[OrderResponse], summary="내 주문 상세 조회")
def 내_주문_상세(
    orderId: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = (
        db.query(Order)
        .options(joinedload(Order.items))                       # N+1 방지(아이템 같이 로딩)
        .filter(Order.id == orderId, Order.user_id == current_user.id)  # 내 주문만 접근
        .first()
    )
    if not order:
        raise_not_found("주문을 찾을 수 없습니다.", "RESOURCE_NOT_FOUND")

    items = [
        OrderItemResponse(
            id=x.id,
            orderId=x.order_id,
            bookId=x.book_id,
            quantity=x.quantity,
            price=x.unit_price,
        )
        for x in order.items
    ]
    return ApiSuccess(
        message="내 주문 상세 조회 성공",
        payload=OrderResponse(
            id=order.id,
            userId=order.user_id,
            status=order.status,
            totalPrice=order.total_price,
            items=items,
        ),
    )


@router.get("/items", response_model=ApiSuccess[list[dict]], summary="내 주문 아이템 전체 조회")
def 내_주문_아이템_전체(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = (
        db.query(OrderItem)
        .join(Order, OrderItem.order_id == Order.id)          # Order.user_id 조건 걸려고 join
        .filter(Order.user_id == current_user.id)
        .all()
    )
    payload = [
        {"id": x.id, "orderId": x.order_id, "bookId": x.book_id, "quantity": x.quantity, "price": x.unit_price}
        for x in items
    ]
    return ApiSuccess(message="내 주문 아이템 조회 성공", payload=payload)


@router.patch("/{orderId}/status", response_model=ApiSuccess[dict], summary="(ADMIN) 주문 상태 변경")
def 주문_상태_변경(
    orderId: int,
    body: OrderStatusUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_roles("ROLE_ADMIN")),      # 관리자만 변경 가능
):
    order = db.query(Order).filter(Order.id == orderId).first()
    if not order:
        raise_not_found("주문을 찾을 수 없습니다.", "RESOURCE_NOT_FOUND")

    order.status = body.status                                 # 상태만 변경
    db.commit()
    return ApiSuccess(message="주문 상태 변경 성공", payload={"orderId": order.id, "status": order.status})