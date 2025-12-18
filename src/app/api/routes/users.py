"""
Users API
- 회원가입, 내 정보 조회수정, 소프트 영구 삭제
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user          # 로그인 사용자 주입
from app.core.errors import raise_conflict         # 이메일 중복 처리
from app.core.security import get_password_hash    # 비밀번호 해시
from app.db.session import get_db                  # DB 세션
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.response import ApiSuccess        # 공통 성공 응답
from app.schemas.openapi_examples import COMMON_ERROR_RESPONSES

router = APIRouter(prefix="/users", tags=["Users"], responses=COMMON_ERROR_RESPONSES)


@router.post("", response_model=ApiSuccess[UserResponse], summary="사용자 회원가입")
def 회원가입(body: UserCreate, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.email == body.email).first()
    if exists:
        raise_conflict("이미 사용 중인 이메일입니다.", "DUPLICATE_RESOURCE")  # 이메일 중복 방지

    user = User(
        email=body.email,
        password_hash=get_password_hash(body.password),  # 비밀번호는 해시 저장
        name=body.name,
        role="ROLE_USER",                                # 기본 사용자 권한
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return ApiSuccess(message="회원가입 성공", payload=user)


@router.get("/me", response_model=ApiSuccess[UserResponse], summary="내 정보 조회")
def 내정보조회(
    current_user: User = Depends(get_current_user),      # 본인 정보만 조회
):
    return ApiSuccess(message="내 정보 조회 성공", payload=current_user)


@router.patch("/me", response_model=ApiSuccess[UserResponse], summary="내 정보 수정")
def 내정보수정(
    body: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.name is not None:
        current_user.name = body.name
    if body.password is not None:
        current_user.password_hash = get_password_hash(body.password)  # 비밀번호 변경 시 재해시

    db.commit()
    db.refresh(current_user)
    return ApiSuccess(message="내 정보 수정 성공", payload=current_user)


@router.delete("/me/soft-delete", response_model=ApiSuccess[dict], summary="소프트 삭제")
def 소프트삭제(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_user.is_active = False                          # 계정 비활성화
    db.commit()
    return ApiSuccess(message="소프트 삭제 성공", payload={"deleted": True})


@router.delete("/me/permanent", response_model=ApiSuccess[dict], summary="영구 삭제")
def 영구삭제(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.delete(current_user)                                 # DB row 완전 삭제
    db.commit()
    return ApiSuccess(message="영구 삭제 성공", payload={"deleted": True})