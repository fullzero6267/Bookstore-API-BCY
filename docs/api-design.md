# API Design (Summary)

Bookstore API 기능 목록

------

## Auth

- 로그인 : POST /api/auth/login (Public)
- 토큰 재발급 : POST /api/auth/reissue (Login)
- 로그아웃 : POST /api/auth/logout (Login)

---

## Users

- 회원가입 : POST /api/users (Public)
- 내 정보 조회 : GET /api/users/me (USER)
- 내 정보 수정 : PATCH /api/users/me (USER)
- 소프트 삭제 : DELETE /api/users/me/soft-delete (USER)
- 영구 삭제 : DELETE /api/users/me/permanent (USER)

---

## Books

- 공개 도서 목록 : GET /api/public/books (Public)
- 도서 목록 : GET /api/books (Public)
- 도서 상세 조회 : GET /api/books/{bookId} (Public)
- 도서 등록 : POST /api/books (ADMIN)
- 도서 수정 : PATCH /api/books/{bookId} (ADMIN)
- 도서 삭제 : DELETE /api/books/{bookId} (ADMIN)

---

## Carts

- 장바구니 조회 : GET /api/carts/items (USER)
- 장바구니 담기 : POST /api/carts/items (USER)
- 장바구니 수량 변경 : PATCH /api/carts/items/{itemId} (USER)
- 장바구니 아이템 삭제 : DELETE /api/carts/items/{itemId} (USER)
- 장바구니 비우기 : DELETE /api/carts/clear (USER)

---

## Orders

- 주문 생성 : POST /api/orders (USER)
- 내 주문 목록 조회 : GET /api/orders (USER)
- 내 주문 상세 조회 : GET /api/orders/{orderId} (USER)
- 내 주문 아이템 전체 조회 : GET /api/orders/items (USER)
- 주문 상태 변경 : PATCH /api/orders/{orderId}/status (ADMIN)

---

## Reviews

- 도서 리뷰 목록 조회 : GET /api/books/{bookId}/reviews (Public)
- 도서 리뷰 작성 : POST /api/books/{bookId}/reviews (USER)
- 내 리뷰 조회 : GET /api/reviews/me (USER)
- 리뷰 수정 : PATCH /api/reviews/{reviewId} (USER)
- 리뷰 삭제 : DELETE /api/reviews/{reviewId} (USER)

---

## Favorites

- 찜 목록 조회 : GET /api/favorites (USER)
- 찜 추가 : POST /api/favorites/{bookId} (USER)
- 찜 삭제 : DELETE /api/favorites/{bookId} (USER)