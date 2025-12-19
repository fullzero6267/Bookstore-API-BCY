# Database Schema (Bookstore)

본 문서는 Bookstore API의 DB 스키마를 **Markdown(.md)** 형태로 정의한다.  
(DBMS: MySQL, ORM: SQLAlchemy 기준)

---

## 0. 공통 규칙

- PK: `id` (INT, Auto Increment)
- FK는 `ON DELETE` 정책을 명시함 (과제용 권장)
- 시간 컬럼은 `created_at`, `updated_at` (UTC 기준) 사용을 전제로 함

---

## 1. users (사용자)

### Columns
- `id` INT PK
- `email` VARCHAR(255) UNIQUE NOT NULL
- `password_hash` VARCHAR(255) NOT NULL
- `name` VARCHAR(100) NOT NULL
- `role` VARCHAR(30) NOT NULL  (예: ROLE_USER, ROLE_ADMIN)
- `is_active` BOOLEAN NOT NULL DEFAULT TRUE
- `created_at` DATETIME NOT NULL
- `updated_at` DATETIME NOT NULL

### Index / Constraints
- UNIQUE(`email`)
- INDEX(`role`)
- INDEX(`is_active`)

---

## 2. books (도서)

### Columns
- `id` INT PK
- `title` VARCHAR(200) NOT NULL
- `author` VARCHAR(120) NOT NULL
- `category` VARCHAR(60) NULL
- `description` TEXT NULL
- `price` INT NOT NULL DEFAULT 0
- `stock` INT NOT NULL DEFAULT 0
- `created_at` DATETIME NOT NULL
- `updated_at` DATETIME NOT NULL

### Index / Constraints
- INDEX(`created_at`)
- INDEX(`price`)
- INDEX(`title`)
- INDEX(`category`)

---

## 3. cart_items (장바구니 아이템)

> 사용자 1명이 같은 책을 장바구니에 **중복 x** `UNIQUE(user_id, book_id)`를 둔다.

### Columns
- `id` INT PK
- `user_id` INT NOT NULL FK -> users.id
- `book_id` INT NOT NULL FK -> books.id
- `quantity` INT NOT NULL DEFAULT 1
- `created_at` DATETIME NOT NULL
- `updated_at` DATETIME NOT NULL

### Constraints
- FK(`user_id`) REFERENCES users(`id`) ON DELETE CASCADE
- FK(`book_id`) REFERENCES books(`id`) ON DELETE CASCADE
- UNIQUE(`user_id`, `book_id`)

### Index
- INDEX(`user_id`)
- INDEX(`book_id`)

---

## 4. favorites (찜)

> 사용자 1명이 같은 책을 **중복으로 찜 x** `UNIQUE(user_id, book_id)`를 둔다.

### Columns
- `id` INT PK
- `user_id` INT NOT NULL FK -> users.id
- `book_id` INT NOT NULL FK -> books.id
- `created_at` DATETIME NOT NULL

### Constraints
- FK(`user_id`) REFERENCES users(`id`) ON DELETE CASCADE
- FK(`book_id`) REFERENCES books(`id`) ON DELETE CASCADE
- UNIQUE(`user_id`, `book_id`)

### Index
- INDEX(`user_id`)
- INDEX(`book_id`)
- INDEX(`created_at`)

---

## 5. orders (주문)

### Columns
- `id` INT PK
- `user_id` INT NOT NULL FK -> users.id
- `status` VARCHAR(30) NOT NULL DEFAULT 'CREATED'  
  - 예: CREATED, PAID, CANCELED, SHIPPED
- `total_price` INT NOT NULL DEFAULT 0
- `created_at` DATETIME NOT NULL
- `updated_at` DATETIME NOT NULL

### Constraints
- FK(`user_id`) REFERENCES users(`id`) ON DELETE CASCADE

### Index
- INDEX(`user_id`)
- INDEX(`status`)
- INDEX(`created_at`)
- INDEX(`total_price`)

---

## 6. order_items (주문 아이템)

> 주문 생성 시점의 가격을 보존하기 위해 `unit_price`를 저장한다.

### Columns
- `id` INT PK
- `order_id` INT NOT NULL FK -> orders.id
- `book_id` INT NOT NULL FK -> books.id
- `quantity` INT NOT NULL
- `unit_price` INT NOT NULL DEFAULT 0
- `created_at` DATETIME NOT NULL

### Constraints
- FK(`order_id`) REFERENCES orders(`id`) ON DELETE CASCADE
- FK(`book_id`) REFERENCES books(`id`) ON DELETE RESTRICT

### Index
- INDEX(`order_id`)
- INDEX(`book_id`)

---

## 7. reviews (리뷰)

> 기본 정책: 한 사용자가 한 책에 여러 리뷰를 허용할 수도 있지만,  
> 과제에서 1개만 허용하려면 `UNIQUE(user_id, book_id)` 추가하면 됨(선택).

### Columns
- `id INT PK`
- `user_id` INT NOT NULL FK -> users.id
- `book_id` INT NOT NULL FK -> books.id
- `rating` INT NOT NULL  (예: 1~5)
- `content` TEXT NOT NULL
- `created_at` DATETIME NOT NULL
- `updated_at` DATETIME NOT NULL

### Constraints
- FK(`user_id`) REFERENCES users(`id`) ON DELETE CASCADE
- FK(`book_id`) REFERENCES books(`id`) ON DELETE CASCADE

### Index
- INDEX(`user_id`)
- INDEX(`book_id`)
- INDEX(`created_at`)

---

## 8. refresh_tokens (리프레시 토큰 저장)

> Refresh Token은 JWT 자체를 저장하지 않고, **jti만 저장**해 폐기(revoke) 가능하게 한다.

### Columns
- `id` INT PK
- `user_id` INT NOT NULL FK -> users.id
- `jti` VARCHAR(64) UNIQUE NOT NULL
- `expires_at` DATETIME NOT NULL
- `is_revoked` BOOLEAN NOT NULL DEFAULT FALSE
- `revoked_at` DATETIME NULL
- `created_at` DATETIME NOT NULL

### Constraints
- FK(`user_id`) REFERENCES users(`id`) ON DELETE CASCADE
- UNIQUE(`jti`)

### Index
- INDEX(`user_id`)
- INDEX(`expires_at`)
- INDEX(`is_revoked`)

---

## 9. 관계 요약 

- users (1) --- (N) cart_items
- users (1) --- (N) favorites
- users (1) --- (N) orders
- users (1) --- (N) reviews
- users (1) --- (N) refresh_tokens

- books (1) --- (N) cart_items
- books (1) --- (N) favorites
- books (1) --- (N) order_items
- books (1) --- (N) reviews

- orders (1) --- (N) order_items

---

## 10. 참고: ERD 텍스트 표현

users
- id PK
- email UNIQUE
- role
- is_active

books
- id PK
- title
- author
- category
- price
- stock

cart_items
- id PK
- user_id FK -> users.id
- book_id FK -> books.id
- UNIQUE(user_id, book_id)

favorites
- id PK
- user_id FK -> users.id
- book_id FK -> books.id
- UNIQUE(user_id, book_id)

orders
- id PK
- user_id FK -> users.id
- status
- total_price

order_items
- id PK
- order_id FK -> orders.id
- book_id FK -> books.id
- quantity
- unit_price

reviews
- id PK
- user_id FK -> users.id
- book_id FK -> books.id
- rating
- content

refresh_tokens
- id PK
- user_id FK -> users.id
- jti UNIQUE
- expires_at
- is_revoked