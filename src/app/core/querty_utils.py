from __future__ import annotations

from typing import Optional, Type
from sqlalchemy import or_
from sqlalchemy.orm import Query


def apply_keyword_filter(  # 문자열 컬럼(keyword) 부분일치 검색 필터
    query: Query,
    model: Type,
    keyword: Optional[str],
    fields: list[str],
) -> Query:
    if not keyword:
        return query

    conditions = []
    for name in fields:
        col = getattr(model, name, None)
        if col is not None:
            conditions.append(col.like(f"%{keyword}%"))

    if not conditions:
        return query

    return query.filter(or_(*conditions))


def apply_sort(  # 정렬 파라미터 처리(field,ASC|DESC + 화이트리스트)
    query: Query,
    sort: Optional[str],
    allowed: dict[str, object],
) -> Query:
    if not sort:
        return query

    parts = [p.strip() for p in sort.split(",")]
    field = parts[0] if len(parts) >= 1 else ""
    direction = (parts[1].upper() if len(parts) >= 2 else "DESC")

    col = allowed.get(field)
    if col is None:
        return query  # 허용되지 않은 정렬은 무시

    if direction == "ASC":
        return query.order_by(col.asc())
    return query.order_by(col.desc())