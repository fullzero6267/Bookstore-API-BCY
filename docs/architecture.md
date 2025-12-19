# Architecture Overview

Bookstore API는 FastAPI 기반의 REST 서버, 
**Router(Controller) / Schema(DTO) / Model(ORM) / Core(공통 유틸) / DB(Session)** 
로 역할을 분리한 구조로 구성함.

---

## 1. 전체 구성

- **API Layer (Routes)**  
  HTTP 요청을 받고, 의존성(인증/DB)을 주입받아 로직을 실행한 뒤 응답을 반환.

- **Schema Layer (Pydantic DTO)**  
  요청/응답 데이터 구조를 정의.

- **Model Layer (SQLAlchemy ORM)**  
  DB 테이블과 매핑되는 엔티티 정의. CRUD는 SQLAlchemy Session을 통해 수행.

- **Core Layer (Common / Cross-cutting)**  
  인증/보안, 공통 에러 포맷, 페이지네이션, 검색/정렬 유틸 등 여러 라우터에서 공통으로 쓰는 기능이 모여있음.

- **DB Layer (Session / Engine)**  
  DB 연결 및 Session 생성 관리.

---

## 2. 디렉토리 구조

(프로젝트 기준: `src/` 아래가 애플리케이션 루트)

```
src/
└─ app/
   ├─ main.py                 # FastAPI 앱 생성, 미들웨어/예외처리, 라우터 include
   ├─ api/
   │  ├─ deps.py              # 의존성 주입(인증/권한 체크)
   │  └─ routes/              # 기능별 라우터(엔드포인트)
   │     ├─ auth.py
   │     ├─ users.py
   │     ├─ books.py
   │     ├─ carts.py
   │     ├─ orders.py
   │     ├─ reviews.py
   │     ├─ favorites.py
   │     └─ admin.py
   ├─ core/
   │  ├─ config.py            # 환경변수(Settings)
   │  ├─ security.py          # JWT/비밀번호 해시/토큰 생성/검증
   │  ├─ errors.py            # 커스텀 예외 표준 에러 응답 유틸
   │  ├─ error_code.py        # 에러 코드
   │  ├─ pagenation.py        # 페이지네이션
   │  └─ query_utils.py       # keyword filter / sort / exact filter 공통 유틸
   ├─ db/
   │  └─ session.py           # DB 엔진/SessionLocal/get_db
   ├─ models/                 # SQLAlchemy ORM 모델
   │  ├─ user.py
   │  ├─ book.py
   │  ├─ cart_item.py
   │  ├─ favorite.py
   │  ├─ order.py             # Order / OrderItem
   │  ├─ review.py
   │  └─ refresh_token.py
   └─ schemas/                # Pydantic DTO (Request/Response)
      ├─ response.py          # 공통 응답(ApiSuccess/ApiError/PageResponse)
      ├─ auth.py
      ├─ user.py
      ├─ book.py
      ├─ cart.py
      ├─ order.py
      ├─ review.py
      └─ favorite.py