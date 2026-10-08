# SQLAlchemy 2.0 Complete Guide

## Overview
SQLAlchemy 2.0 uses modern Python typing with Mapped[] and mapped_column().

## Database Setup
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.orm import Session

DATABASE_URL = "postgresql://user:pass@localhost:5432/mydb"
engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass
```

## Model Definition (SQLAlchemy 2.0 Style)
```python
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="USER")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    orders: Mapped[list["Order"]] = relationship(back_populates="user")

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    total: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict)

    user: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order")
```

## CRUD Operations (Modern 2.0 Syntax)
```python
from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session

def create_user(db: Session, email: str, password: str) -> User:
    user = User(email=email, hashed_password=password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user(db: Session, user_id: uuid.UUID) -> User | None:
    stmt = select(User).where(User.id == user_id)
    return db.execute(stmt).scalar_one_or_none()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    stmt = select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
    return list(db.execute(stmt).scalars().all())

def update_user(db: Session, user_id: uuid.UUID, **kwargs) -> User | None:
    stmt = update(User).where(User.id == user_id).values(**kwargs).returning(User)
    result = db.execute(stmt).scalar_one_or_none()
    db.commit()
    return result

def delete_user(db: Session, user_id: uuid.UUID) -> bool:
    stmt = delete(User).where(User.id == user_id)
    result = db.execute(stmt)
    db.commit()
    return result.rowcount > 0
```

## Relationships and Eager Loading
```python
from sqlalchemy.orm import selectinload, joinedload

def get_user_with_orders(db: Session, user_id: uuid.UUID) -> User | None:
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.orders))
    )
    return db.execute(stmt).scalar_one_or_none()

def get_order_with_user(db: Session, order_id: uuid.UUID) -> Order | None:
    stmt = (
        select(Order)
        .where(Order.id == order_id)
        .options(joinedload(Order.user))
    )
    return db.execute(stmt).unique().scalar_one_or_none()
```

## Database Session Dependency (FastAPI)
```python
from fastapi import Depends
from typing import Generator

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```
