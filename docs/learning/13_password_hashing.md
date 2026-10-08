# Password Hashing and Salting (bcrypt)

## What is Hashing and Salting?
- HASHING: One-way function that converts password to fixed-length string
- SALTING: Adding random data before hashing so same passwords produce different hashes
- BCRYPT: Industry standard, includes built-in salt, adaptive (can increase rounds)

## Install
```bash
pip install passlib[bcrypt]
```

## Implementation
```python
from passlib.context import CryptContext

# Create password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

## How bcrypt Works
```
Input: "mypassword123"
1. Generate random salt: "$2b$12$LJ3m4ys3Lk0TSwHkV..."
2. Combine: salt + password
3. Run bcrypt algorithm 4096 rounds (2^12)
4. Output: $2b$12$LJ3m4ys3Lk0TSwHkV... (60 chars)

Same password + different salt = different hash
This prevents rainbow table attacks
```

## Usage in Signup
```python
@router.post("/signup")
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    hashed = hash_password(payload.password)
    user = User(email=payload.email, hashed_password=hashed, role="USER")
    db.add(user)
    db.commit()
    return user
```

## Usage in Login
```python
@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == form_data.username)).scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # Generate tokens...
```

## Important Rules
1. NEVER store plain text passwords
2. NEVER log passwords (even hashed)
3. NEVER send hashed password in API response (use response_model to exclude)
4. ALWAYS use bcrypt or argon2 (not SHA256 or MD5)
5. bcrypt hash includes the salt, so you only store one field
6. Increase work factor over time as hardware gets faster
