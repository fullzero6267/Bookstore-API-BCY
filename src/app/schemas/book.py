from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class BookCreate(BaseModel):  # 도서 등록 요청 DTO
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Clean Code",
                    "author": "Robert C. Martin",
                    "category": "programming",
                    "description": "A Handbook of Agile Software Craftsmanship",
                    "price": 25000,
                    "stock": 50,
                }
            ]
        }
    )
    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=1, max_length=120)
    category: Optional[str] = Field(default=None, max_length=60)
    description: Optional[str] = None
    price: int = Field(default=0, ge=0)
    stock: int = Field(default=0, ge=0)


class BookUpdate(BaseModel):  # 도서 수정 요청 DTO(PATCH)
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    author: Optional[str] = Field(default=None, min_length=1, max_length=120)
    category: Optional[str] = Field(default=None, max_length=60)
    description: Optional[str] = None
    price: Optional[int] = Field(default=None, ge=0)
    stock: Optional[int] = Field(default=None, ge=0)


class BookResponse(BaseModel):  # 도서 응답 DTO
    id: int
    title: str
    author: str
    category: Optional[str] = None
    description: Optional[str] = None
    price: int
    stock: int

    class Config:  # ORM 객체 응답 변환 허용
        from_attributes = True