# FastAPI Security and Middleware Complete Guide

## Middleware Types
1. CORS Middleware - Cross-Origin Resource Sharing
2. TrustedHost Middleware - Prevent host header attacks
3. Custom Security Headers - XSS, CSRF, clickjacking protection
4. IP Whitelisting - Restrict by IP address
5. Request/Response Logging - Audit trail

## Security Middleware Setup
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from core.config import settings

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

def setup_security_middleware(app: FastAPI) -> None:
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
        expose_headers=["Location", "Content-Disposition"],
        max_age=600,
    )
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )
```

## IP Whitelisting Dependency
```python
from fastapi import Depends, HTTPException, Request
from core.config import settings

def verify_allowed_ip(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    if client_ip not in settings.ALLOWED_IPS:
        raise HTTPException(status_code=403, detail=f"IP {client_ip} is not allowed")
```

## Method-Level Security (RBAC)
```python
from fastapi import Depends
from core.security import get_current_user

def require_roles(*allowed_roles: str):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return role_checker

# Usage in routes:
@router.post(
    "/query-database",
    dependencies=[
        Depends(verify_allowed_ip),
        Depends(require_roles("SUPER_ADMIN")),
    ]
)
def query_database():
    return {"message": "Admin only endpoint"}
```

## RBAC Roles
```
SUPER_ADMIN  - Full access to everything
ADMIN        - Administrative access
DOCTOR       - Medical staff access
NURSE        - Limited medical access
RECEPTIONIST - Front desk access
USER         - Standard user access
```

## Middleware Order (Important!)
Middleware runs in REVERSE order of registration:
1. Last added = First to process request
2. First added = Last to process request
3. Security headers should be added FIRST (outermost)
4. CORS should be added LAST (innermost for preflight)
