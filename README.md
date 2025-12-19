# Bookstore API

FastAPI 기반의 온라인 서점 api  
사용자 인증, 도서 관리, 장바구니, 주문, 리뷰, 찜 기능.

---

## 1. 프로젝트 개요

### 문제 정의
온라인 서점 서비스에 필요한 기능을 REST API 형태로 설계하고,
실제로 배포 가능한 서버로 구현한다.

### 주요 기능
- JWT 기반 인증/인가 (Access / Refresh Token)
- 사용자 회원가입 및 정보 관리
- 도서 조회 / 등록 / 수정 / 삭제
- 장바구니 기능
- 주문 생성 및 조회
- 리뷰 및 찜 기능
- 관리자(Admin) 전용 관리 기능

---

## 2. 실행 방법

### 로컬 실행 (FastAPI) < ssh로 연동해서 실행할때는 조금 다름

```bash
# 의존성 설치
pip install -r requirements.txt
(requirements 파일에 필요한 걸 모두 적어놓음)

# DB 마이그레이션
alembic upgrade head

# 초기 데이터 시드
python seed.py

# 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

---

## 3. 환경변수 
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=bookstore_user
DB_PASSWORD=bookstore_password
DB_NAME=bookstore

JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

CORS_ORIGINS=
```

---

## 4. 배포주소 

- Base URL
>http://113.198.66.68:10099
- Swagger URL
>http://113.198.66.68:10099/docs
- Health URL
>http://113.198.66.68:10099/health

---

## 5. 인증 플로우 설명
    1. 로그인 시 Access Token / Refresh Token 발급
	2. Access Token으로 API 요청 인증
	3. Access Token 만료 시 Refresh Token으로 재발급
	4. 로그아웃 시 Refresh Token 폐기(DB 기준)

	• Access Token: Authorization Header 또는 Cookie
	• Refresh Token: Cookie 기반

---

## 6. 역학/권한

    ROLE_USER 일반 사용자
    ROLE_ADMIN 관리자

***권한별 접근 API***
```    
• USER: 장바구니, 주문, 리뷰, 찜
• ADMIN: 도서 관리, 사용자 관리, 주문 상태 변경
```
```
괄리자 계정은 따로 생성불가, 회원가입으로 일반계정만 생성가능
```