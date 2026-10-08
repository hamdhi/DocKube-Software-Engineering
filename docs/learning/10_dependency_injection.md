# Dependency Injection and Database Session Guide

## What is Dependency Injection (DI)?
DI is a pattern where dependencies (like DB sessions, current user, config) are injected into functions rather than created inside them. FastAPI does this automatically via Depends().

## Database Session DI
```python
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# In routes:
@router.get("/users/")
def get_users(db: Session = Depends(get_db)):
    return db.execute(select(User)).scalars().all()
```

## What is `yield`?
`yield` turns a function into a generator. In DI:
- Code BEFORE yield runs first (setup: create DB session)
- The yielded value is injected into the route
- Code AFTER yield runs when the request finishes (cleanup: close session)

```python
def get_db():
    db = SessionLocal()     # Setup
    try:
        yield db            # Inject this into the route
    finally:
        db.close()          # Cleanup (always runs, even on error)
```

## Commit vs Rollback
```python
# COMMIT: Permanently save changes to database
db.add(new_user)
db.commit()  # Now the row exists in the database

# ROLLBACK: Undo all uncommitted changes
try:
    db.add(user)
    db.commit()
except IntegrityError:
    db.rollback()  # Undo the add, session is clean again
```

## Try/Except Pattern
```python
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

@router.post("/users/")
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        user = User(**payload.model_dump())
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="User already exists")
```

## Common Dependencies
```python
# 1. Database session
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 2. Current user (from JWT)
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_token(token)
    return db.get(User, uuid.UUID(payload["sub"]))

# 3. Pagination
class PaginationDep:
    def __init__(self, page: int = 1, per_page: int = 20):
        self.page = page
        self.per_page = per_page
        self.offset = (page - 1) * per_page

# 4. Settings
def get_settings() -> Settings:
    return Settings()

# Chained dependencies (get_current_user depends on get_db):
@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    return user
```

## Dependency Hierarchy
```
get_current_user depends on --> get_db (session) + oauth2_scheme (token)
Route depends on --> get_current_user (user object)
```

## Key Rules
1. ALWAYS use `yield` for resources that need cleanup (DB, file handles)
2. ALWAYS call `db.rollback()` on error before raising exception
3. NEVER share a session between requests (create new one per request)
4. Use `db.refresh(obj)` after commit to get auto-generated fields (id, timestamps)
5. Use `expire_on_commit=False` to access objects after commit without re-query
