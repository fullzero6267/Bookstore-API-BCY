from __future__ import annotations

from pydantic import BaseModel, Field


class CartItemCreate(BaseModel):  # 장바구니 담기 요청 DTO
    bookId: int = Field(..., ge=1)
    quantity: int = Field(default=1, ge=1, le=999)


class CartItemUpdate(BaseModel):  # 장바구니 수량 변경 요청 DTO
    quantity: int = Field(..., ge=1, le=999)


class CartItemResponse(BaseModel):  # 장바구니 아이템 응답 DTO
    id: int
    userId: int
    bookId: int
    quantity: int

    class Config:  # ORM 객체 응답 변환 허용
        from_attributes = True