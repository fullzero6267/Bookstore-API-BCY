from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class OrderItemCreate(BaseModel):  # 주문 생성 시 아이템 단위 DTO(data transfer object)
    bookId: int = Field(..., ge=1)
    quantity: int = Field(default=1, ge=1, le=999)


class OrderCreate(BaseModel):  # 주문 생성 요청 DTO
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "items": [
                        {"bookId": 1, "quantity": 2},
                        {"bookId": 3, "quantity": 1},
                    ],
                    "address": "Seoul, Korea",
                    "paymentMethod": "CARD",
                }
            ]
        }
    )
    items: List[OrderItemCreate] = Field(..., min_length=1)


class OrderStatusUpdate(BaseModel):  # 주문 상태 변경 요청 DTO(ADMIN)
    status: str = Field(..., min_length=1, max_length=30)


class OrderItemResponse(BaseModel):  # 주문 아이템 응답 DTO
    id: int
    orderId: int
    bookId: int
    quantity: int
    price: int

    class Config:  # ORM 객체 -> 응답 변환 허용
        from_attributes = True


class OrderResponse(BaseModel):  # 주문 응답 DTO(목록/상세 공용)
    id: int
    userId: int
    status: str
    totalPrice: int
    items: Optional[List[OrderItemResponse]] = None  # 목록 조회 시 None

    class Config:  # ORM 객체 응답 변환 허용
        from_attributes = True