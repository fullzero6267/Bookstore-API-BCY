from __future__ import annotations

from datetime import datetime
from typing import Optional, Type, Any

from sqlalchemy import or_
from sqlalchemy.orm import Query


def apply_keyword_filter(query: Query, model: Type, keyword: Optional[str], fields: list[str]) -> Query:
    """keyword 검색 공통 유틸(부분일치, 대소문자 무시)
    - fields: ["title", "author"] 처럼 문자열 컬럼명 목록
    """
    if not keyword:
        return query

    keyword = keyword.strip()
    if not keyword:
        return query

    conditions = []
    for name in fields:
        col = getattr(model, name, None)
        if col is not None:
            conditions.append(col.ilike(f"%{keyword}%"))

    if not conditions:
        return query

    return query.filter(or_(*conditions))


def apply_exact_filter(query: Query, model: Type, field: str, value: Optional[Any]) -> Query:
    """정확 일치 필터 공통 유틸 (예: category=status)"""
    if value is None or value == "":
        return query
    col = getattr(model, field, None)
    if col is None:
        return query
    return query.filter(col == value)


def apply_datetime_range(
    query: Query,
    model: Type,
    field: str,
    date_from: Optional[datetime],
    date_to: Optional[datetime],
) -> Query:
    """datetime 범위 필터 (created_at 등)"""
    col = getattr(model, field, None)
    if col is None:
        return query
    if date_from is not None:
        query = query.filter(col >= date_from)
    if date_to is not None:
        query = query.filter(col <= date_to)
    return query


def apply_sort(query: Query, sort: Optional[str], allowed: dict[str, Any], default: Optional[str] = None) -> Query:
    """sort=field,ASC|DESC (화이트리스트)
    - allowed: {"created_at": Model.created_at, "price": Model.price}
    - default: sort 미지정 시 적용할 기본값(예: "created_at,DESC")
    """
    sort_value = sort or default
    if not sort_value:
        return query

    parts = [p.strip() for p in sort_value.split(",")]
    field = parts[0] if len(parts) >= 1 else ""
    direction = (parts[1].upper() if len(parts) >= 2 else "DESC")

    col = allowed.get(field)
    if col is None:
        return query  # 허용되지 않은 정렬은 무시(안전)

    if direction == "ASC":
        return query.order_by(col.asc())
    return query.order_by(col.desc())
