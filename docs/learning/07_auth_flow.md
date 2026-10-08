# Login, Logout, Refresh Token Complete Flow

## Auth Routes (api/v1/auth.py)
```python
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import (
    create_access_token, create_refresh_token, hash_refresh_token,
    verify_password, get_current_user,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    stmt = select(User).where(User.email == form_data.username)
    user = db.execute(stmt).scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    token_data = {"sub": str(user.id), "role": user.role, "ver": user.token_version}
    access_token = create_access_token(token_data, timedelta(minutes=15))
    refresh_token, refresh_token_hash = create_refresh_token()
    _create_refresh_session(db, user.id, refresh_token_hash)
    db.commit()
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    token_hash = hash_refresh_token(payload.refresh_token)
    session = db.execute(
        select(RefreshTokenSession)
        .where(RefreshTokenSession.token_hash == token_hash)
        .with_for_update()
    ).scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if session.revoked_at:
        _revoke_token_family(db, session.family_id, now, "reuse_detected")
        db.commit()
        raise HTTPException(status_code=401, detail="Refresh token reuse detected")
    if session.expires_at <= now:
        session.revoked_at = now
        session.revoked_reason = "expired"
        db.commit()
        raise HTTPException(status_code=401, detail="Refresh token has expired")
    user = db.get(User, session.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User is not available")
    new_refresh_token, new_refresh_hash = create_refresh_token()
    session.last_used_at = now
    session.revoked_at = now
    session.revoked_reason = "rotated"
    session.replaced_by_hash = new_refresh_hash
    _create_refresh_session(db, user.id, new_refresh_hash, session.family_id)
    db.commit()
    token_data = {"sub": str(user.id), "role": user.role, "ver": user.token_version}
    return {
        "access_token": create_access_token(token_data, timedelta(minutes=15)),
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }

@router.post("/logout")
def logout(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = _get_token_user_for_route(current_user, db)
    user.token_version += 1
    _revoke_all_user_sessions(db, user.id, datetime.now(timezone.utc), "logout_all")
    db.commit()
    return {"message": "Successfully logged out from all devices"}

def _create_refresh_session(db, user_id, token_hash, family_id=None):
    now = datetime.now(timezone.utc)
    db.add(RefreshTokenSession(
        user_id=user_id, token_hash=token_hash,
        family_id=family_id or uuid.uuid4(),
        created_at=now, expires_at=now + timedelta(days=7),
    ))

def _revoke_token_family(db, family_id, revoked_at, reason):
    db.execute(
        update(RefreshTokenSession)
        .where(RefreshTokenSession.family_id == family_id,
               RefreshTokenSession.revoked_at.is_(None))
        .values(revoked_at=revoked_at, revoked_reason=reason)
    )

def _revoke_all_user_sessions(db, user_id, revoked_at, reason):
    db.execute(
        update(RefreshTokenSession)
        .where(RefreshTokenSession.user_id == user_id,
               RefreshTokenSession.revoked_at.is_(None))
        .values(revoked_at=revoked_at, revoked_reason=reason)
    )
```

## Authentication Flow Diagram
```
LOGIN FLOW:
User --> POST /login (email + password)
     --> Server verifies password hash
     --> Generate access_token (JWT, 15 min)
     --> Generate refresh_token (random, 7 days)
     --> Store refresh_token hash in DB
     --> Return both tokens

API REQUEST FLOW:
Client --> GET /users/me (Bearer access_token)
        --> Server validates JWT signature + expiry
        --> Check token_version matches DB
        --> Return data

TOKEN REFRESH FLOW:
Client --> POST /refresh (refresh_token)
        --> Server looks up token hash in DB
        --> Check not revoked, not expired
        --> Revoke old token (mark as rotated)
        --> Issue new refresh_token
        --> Return new access_token + refresh_token

LOGOUT FLOW:
Client --> POST /logout (Bearer access_token)
        --> Increment user.token_version
        --> Revoke all refresh sessions for user
        --> All existing tokens now invalid
```

## Why Refresh Token Rotation?
1. Reuse Detection: If a stolen refresh token is used, the entire token family is revoked
2. Short Access Tokens: 15 min expiry limits damage from stolen tokens
3. Family Tracking: Each login creates a family; rotation keeps the family alive
4. Force Logout: token_version increment invalidates all tokens instantly
