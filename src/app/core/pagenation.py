from __future__ import annotations

from typing import Any, Optional
from sqlalchemy.orm import Query


def paginate(  # 공통 페이지네이션 처리
    query: Query,
    page: int = 0,
    size: int = 20,
    sort: Optional[str] = None,
) -> dict[str, Any]:

    if page < 0:
        page = 0
    if size <= 0:
        size = 20
    if size > 100:
        size = 100

    total = query.count()                    # 전체 개수
    total_pages = (total + size - 1) // size # 전체 페이지 수
    items = query.offset(page * size).limit(size).all()  # 현재 페이지 데이터

    return {
        "content": items,                    # 현재 페이지 결과
        "page": page,
        "size": size,
        "totalElements": total,
        "totalPages": total_pages,
        "sort": sort or "",                  # 요청된 정렬 정보(표시용)
    }