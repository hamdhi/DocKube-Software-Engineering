# Pagination Complete Guide

## Query Parameter Schema
```python
from pydantic import BaseModel, Field

class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool
```

## Pagination Dependency
```python
from fastapi import Depends, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

def paginate(
    db: Session,
    model,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    order_by=None,
):
    offset = (page - 1) * per_page

    # Count total
    total = db.execute(select(func.count()).select_from(model)).scalar()

    # Get items
    stmt = select(model).offset(offset).limit(per_page)
    if order_by is not None:
        stmt = stmt.order_by(order_by)
    items = list(db.execute(stmt).scalars().all())

    pages = (total + per_page - 1) // per_page  # Ceiling division

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1,
    }
```

## Usage in Routes
```python
from fastapi import APIRouter, Depends, Query
from typing import TypeVar, Generic
from pydantic import BaseModel

router = APIRouter()

T = TypeVar("T")

class StandardResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: str = "Success"

@router.get("/users/", response_model=StandardResponse[PaginatedResponse])
def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    result = paginate(db, User, page, per_page, order_by=User.created_at.desc())
    return StandardResponse(data=result)

@router.get("/users/{user_id}/orders")
def list_user_orders(
    user_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * per_page
    total = db.execute(
        select(func.count()).select_from(Order).where(Order.user_id == user_id)
    ).scalar()
    items = db.execute(
        select(Order)
        .where(Order.user_id == user_id)
        .offset(offset)
        .limit(per_page)
        .order_by(Order.created_at.desc())
    ).scalars().all()
    return {
        "items": items, "total": total, "page": page,
        "per_page": per_page, "pages": (total + per_page - 1) // per_page,
    }
```

## Cursor-Based Pagination (For Large Datasets)
```python
@router.get("/messages/")
def list_messages(
    cursor: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(Message).order_by(Message.created_at.desc()).limit(limit + 1)
    if cursor:
        stmt = stmt.where(Message.id > uuid.UUID(cursor))
    items = list(db.execute(stmt).scalars().all())

    has_next = len(items) > limit
    if has_next:
        items = items[:limit]

    next_cursor = str(items[-1].id) if items and has_next else None

    return {"items": items, "next_cursor": next_cursor, "has_next": has_next}
```

## Key Points
- Always limit per_page (prevent loading entire table)
- Use offset for small datasets, cursor for large ones
- Return total count for UI pagination controls
- has_next/has_prev help frontend disable buttons
- Default order matters for consistent pagination
