# JWT Authentication Complete Guide

## Install Dependencies
```bash
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
```

## Security Module (core/security.py)
```python
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets
import hashlib

# Configuration
SECRET_KEY = "your-super-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Access Token (JWT)
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Refresh Token (Random string, stored hashed in DB)
def create_refresh_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token, token_hash

def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
```

## Token Verification Dependency
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        token_version = payload.get("ver", 0)
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.get(User, uuid.UUID(user_id))
    if user is None or not user.is_active:
        raise credentials_exception
    if user.token_version != token_version:
        raise HTTPException(status_code=401, detail="Token has been revoked")
    return user

def get_optional_current_user(token: str | None = Depends(oauth2_scheme)) -> dict | None:
    if not token:
        return None
    try:
        return decode_token(token)
    except JWTError:
        return None
```

## Token Payload Structure
```python
# Access token payload:
{
    "sub": "user-uuid-here",       # Subject (user ID)
    "role": "SUPER_ADMIN",         # User role for RBAC
    "ver": 0,                      # Token version (for logout-all)
    "exp": 1234567890,             # Expiry timestamp
    "type": "access"               # Token type
}

# Refresh token: Just a random string
# Stored in DB as SHA-256 hash, never store the raw token
```

## How JWT Works (Flow)
```
1. User logs in with email/password
2. Server verifies credentials
3. Server creates access_token (JWT, 15 min expiry)
4. Server creates refresh_token (random, 7 days expiry)
5. Server stores refresh_token hash in database
6. Both tokens returned to client
7. Client sends access_token in Authorization header
8. Server validates JWT signature and expiry
9. If access_token expired, client uses refresh_token to get new one
```

## Token Version for Force Logout
```python
# In User model:
token_version: Mapped[int] = mapped_column(default=0, nullable=False)

# On "logout all devices":
user.token_version += 1
db.commit()
# All existing tokens now fail because payload["ver"] != user.token_version
```
