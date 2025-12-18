from __future__ import annotations

from pydantic import BaseModel


class FavoriteResponse(BaseModel):
    id: int
    user_id: int
    book_id: int

    class Config:
        from_attributes = True
