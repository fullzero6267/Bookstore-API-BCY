from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.db.base import Base


class Book(Base):
    """도서 엔티티"""
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(200), nullable=False, index=True)
    author = Column(String(120), nullable=False, index=True)
    category = Column(String(60), nullable=True, index=True)

    description = Column(Text, nullable=True)

    price = Column(Integer, nullable=False, default=0)
    stock = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())