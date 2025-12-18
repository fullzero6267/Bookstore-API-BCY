from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Alembic이 테이블을 인식하도록 모델 import 모음 (noqa)
from app.models.refresh_token import RefreshToken
from app.models.book import Book
from app.models.order import Order
from app.models.favorite import Favorite
from app.models.review import Review
from app.models.cart_item import CartItem  # noqa: F401