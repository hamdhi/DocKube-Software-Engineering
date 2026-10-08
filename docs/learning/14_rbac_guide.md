# RBAC (Role-Based Access Control) Complete Guide

## What is RBAC?
Instead of giving each user individual permissions, you assign roles, and roles have permissions. Users get roles, not permissions directly.

```
User --> has Role --> has Permissions
Doctor --> DOCTOR role --> can view_patients, edit_records
Nurse --> NURSE role --> can view_patients, add_notes
```

## User Model with Role
```python
import uuid
from sqlalchemy import String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="USER")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    token_version: Mapped[int] = mapped_column(default=0, nullable=False)
```

## Roles: Enum vs String vs UUID

### Option 1: String (Simple, What your project uses)
```python
role: Mapped[str] = mapped_column(String(50), default="USER")
# Values: "SUPER_ADMIN", "ADMIN", "DOCTOR", "NURSE", "USER"
# Pro: Simple, human readable
# Con: No validation, typos possible
```

### Option 2: Python Enum (Better validation)
```python
import enum
from sqlalchemy import Enum as SQLEnum

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    DOCTOR = "DOCTOR"
    NURSE = "NURSE"
    USER = "USER"

class User(Base):
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)

# Usage:
if user.role == UserRole.DOCTOR:
    ...
# Pro: Type safe, autocomplete, validation
# Con: Slightly more code
```

### Option 3: Separate Roles Table (Most Flexible)
```python
class Role(Base):
    __tablename__ = "roles"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True)  # "DOCTOR"
    permissions: Mapped[list] = mapped_column(JSONB, default=list)  # ["view_patients", "edit_records"]

class UserRole(Base):  # Junction table
    __tablename__ = "user_roles"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id"))

# Pro: Can assign multiple roles, dynamic permissions
# Con: More complex, requires joins
```

## Role Check Dependency
```python
from fastapi import Depends, HTTPException
from core.security import get_current_user

def require_roles(*allowed_roles: str):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

# Convenience functions
require_super_admin = require_roles("SUPER_ADMIN")
require_admin = require_roles("SUPER_ADMIN", "ADMIN")
require_medical_staff = require_roles("SUPER_ADMIN", "ADMIN", "DOCTOR", "NURSE")
```

## How Roles are Assigned in Production

### Method 1: Admin assigns (Most Common)
```python
@router.put("/users/{user_id}/role")
def assign_role(
    user_id: str,
    new_role: str,
    admin: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    user = db.get(User, uuid.UUID(user_id))
    if not user:
        raise UserNotFound("User not found")
    user.role = new_role
    user.token_version += 1  # Force re-login with new role
    db.commit()
    return {"message": f"Role updated to {new_role}"}
```

### Method 2: Self-registration (Default role)
```python
@router.post("/signup")
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role="USER",  # Everyone starts as USER
    )
    db.add(user)
    db.commit()
    return user
```

### Method 3: Bootstrap (First SUPER_ADMIN)
```python
# In migration or startup script:
def create_first_admin(db: Session):
    admin = User(
        email="admin@example.com",
        hashed_password=hash_password("changeme123"),
        role="SUPER_ADMIN",
    )
    db.add(admin)
    db.commit()
```

## Role vs Permission Matrix
```
Role           | view | create | edit | delete | admin
SUPER_ADMIN    |  X   |   X    |  X   |   X    |  X
ADMIN          |  X   |   X    |  X   |   X    |
DOCTOR         |  X   |   X    |  X   |        |
NURSE          |  X   |   X    |      |        |
USER           |  X   |        |      |        |
```

## Recommendation for Your Project
Use **String roles** (what you already have) for simplicity. Switch to **Enum** when you want IDE autocomplete and typo protection. Only use **separate table** if users need multiple roles or dynamic permissions.
