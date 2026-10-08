# Async vs Def Complete Guide

## What is the Difference?
`def` = synchronous (blocking) function
`async def` = asynchronous (non-blocking) function

## When to Use `def` (Synchronous)
```python
# Use def when:
# 1. Doing CPU-bound work (calculations, image processing)
# 2. Using blocking libraries (most DB drivers, file I/O)
# 3. SQLAlchemy sync sessions
# 4. Simple routes that don't need concurrency

@router.get("/users/")
def get_users(db: Session = Depends(get_db)):  # def, not async def
    return db.execute(select(User)).scalars().all()
```

## When to Use `async def` (Asynchronous)
```python
# Use async def when:
# 1. Doing I/O-bound work (API calls, HTTP requests)
# 2. Using async libraries (httpx, asyncpg, aiohttp)
# 3. SQLAlchemy async sessions
# 4. Need concurrency (handle multiple requests simultaneously)

@router.get("/external-data")
async def get_external_data():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
    return response.json()
```

## SQLAlchemy Sync vs Async
```python
# SYNC (use with def)
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

@router.get("/users/")
def get_users(db: Session = Depends(get_db)):  # def
    return db.execute(select(User)).scalars().all()

# ASYNC (use with async def)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

async_engine = create_async_engine(DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"))
AsyncSessionLocal = async_sessionmaker(bind=async_engine, expire_on_commit=False)

async def get_async_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.get("/users/")
async def get_users(db: AsyncSession = Depends(get_async_db)):  # async def
    result = await db.execute(select(User))
    return result.scalars().all()
```

## Concurrency Example
```python
import asyncio
import httpx

# SLOW: Sequential (3 seconds total)
@router.get("/dashboard-slow")
async def dashboard_slow():
    async with httpx.AsyncClient() as client:
        users = await client.get("http://api/users")      # 1 sec
        orders = await client.get("http://api/orders")     # 1 sec
        stats = await client.get("http://api/stats")       # 1 sec
    return {"users": users.json(), "orders": orders.json(), "stats": stats.json()}

# FAST: Concurrent (1 second total)
@router.get("/dashboard-fast")
async def dashboard_fast():
    async with httpx.AsyncClient() as client:
        users_task = client.get("http://api/users")
        orders_task = client.get("http://api/orders")
        stats_task = client.get("http://api/stats")
        users, orders, stats = await asyncio.gather(users_task, orders_task, stats_task)
    return {"users": users.json(), "orders": orders.json(), "stats": stats.json()}
```

## Rules of Thumb
| Scenario | Use | Why |
|----------|-----|-----|
| SQLAlchemy sync DB | def | Blocking driver |
| SQLAlchemy async DB | async def | Non-blocking driver |
| External API calls | async def | I/O bound, can be concurrent |
| CPU calculations | def | CPU bound, async doesn't help |
| File upload | def | Blocking I/O |
| Simple CRUD | def | No concurrency benefit |
| Calling other services | async def | Can parallelize |

## CRITICAL: Don't Mix
```python
# WRONG: async def with sync DB (blocks the event loop)
@router.get("/bad")
async def bad(db: Session = Depends(get_db)):
    return db.execute(select(User)).scalars().all()  # Blocks event loop!

# CORRECT: def with sync DB
@router.get("/good")
def good(db: Session = Depends(get_db)):
    return db.execute(select(User)).scalars().all()

# OR: async def with async DB
@router.get("/good-async")
async def good_async(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(User))
    return result.scalars().all()
```
