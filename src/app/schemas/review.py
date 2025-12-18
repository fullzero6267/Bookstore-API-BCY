from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ReviewCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"bookId": 1, "rating": 5, "content": "재밌고 유익한 책이에요."}]})
    rating: int = Field(default=5, ge=1, le=5)
    content: Optional[str] = None


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    content: Optional[str] = None


class ReviewResponse(BaseModel):
    id: int
    user_id: int
    book_id: int
    rating: int
    content: Optional[str] = None

    class Config:
        from_attributes = True
