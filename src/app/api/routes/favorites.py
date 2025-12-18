"""
Favorites(찜) API
내 찜 목록 / 찜 추가 / 찜 삭제
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user          # 로그인 사용자 주입
from app.core.errors import raise_conflict         # 중복 찜 방지용(409)
from app.core.pagenation import paginate           # 공통 페이지네이션
from app.core.query_utils import apply_sort        # sort 화이트리스트 처리
from app.db.session import get_db                  # DB 세션
from app.models.favorite import Favorite           # 찜 테이블
from app.models.user import User
from app.schemas.favorite import FavoriteResponse  # 찜 응답 DTO
from app.schemas.response import ApiSuccess        # 공통 성공 응답
from app.schemas.openapi_examples import COMMON_ERROR_RESPONSES

router = APIRouter(prefix="/favorites", tags=["Favorites"], responses=COMMON_ERROR_RESPONSES)  # /api는 main에서


@router.get("", response_model=ApiSuccess[dict], summary="내 찜 목록 조회")
def 내_찜_목록(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    sort: str = Query("created_at,DESC"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user), # 내 찜만 조회
):
    q = db.query(Favorite).filter(Favorite.user_id == current_user.id)  # 사용자 기준 필터
    q = apply_sort(                                                     # 정렬: 허용된 필드만
        q,
        sort,
        allowed={"created_at": Favorite.created_at, "id": Favorite.id},
        default="created_at,DESC",
    )
    page_dict = paginate(q, page=page, size=size, sort=sort)            # page/size 적용
    page_dict["content"] = [FavoriteResponse.model_validate(x) for x in page_dict["content"]]  # 응답 DTO 변환
    return ApiSuccess(message="내 찜 목록 조회 성공", payload=page_dict)


@router.post("/{bookId}", response_model=ApiSuccess[dict], summary="찜 추가")
def 찜_추가(
    bookId: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exists = (
        db.query(Favorite)
        .filter(Favorite.user_id == current_user.id, Favorite.book_id == bookId)
        .first()
    )
    if exists:
        raise_conflict("이미 찜한 도서입니다.", "DUPLICATE_RESOURCE")    # 중복 찜 막기

    fav = Favorite(user_id=current_user.id, book_id=bookId)             # 찜 생성
    db.add(fav)
    db.commit()
    return ApiSuccess(message="찜 추가 성공", payload={"bookId": bookId})


@router.delete("/{bookId}", response_model=ApiSuccess[dict], summary="찜 삭제")
def 찜_삭제(
    bookId: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    fav = (
        db.query(Favorite)
        .filter(Favorite.user_id == current_user.id, Favorite.book_id == bookId)
        .first()
    )
    if fav:
        db.delete(fav)                                                  # 있으면 삭제
        db.commit()
    return ApiSuccess(message="찜 삭제 성공", payload={"bookId": bookId, "deleted": True})