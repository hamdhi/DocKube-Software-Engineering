# Global Exception Handlers Complete Guide

## Setup and Configuration
```python
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)

class APIException(Exception):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class UserNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND

class DataNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND

class DataAlreadyExists(APIException):
    status_code = status.HTTP_409_CONFLICT

class Unauthorized(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED

class Forbidden(APIException):
    status_code = status.HTTP_403_FORBIDDEN
```

## Exception Handlers
```python
async def app_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    logger.error(f"API Error at {request.url}: {exc.message}", exc_info=True)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_type": type(exc).__name__,
            "message": exc.message,
        }
    )

async def global_catch_all_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"UNHANDLED FATAL ERROR at {request.url}: {repr(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_type": "InternalServerError",
            "message": "Something went wrong on our end.",
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    validation_errors = exc.errors()
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_type": "ValidationError",
            "message": "The data provided is invalid.",
            "details": validation_errors,
        }
    )

async def sqlalchemy_integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    logger.error(f"Database Integrity Error at {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error_type": "DatabaseConflict",
            "message": "A data conflict occurred. This record might already exist.",
        }
    )

app = FastAPI()
app.add_exception_handler(APIException, app_exception_handler)
app.add_exception_handler(Exception, global_catch_all_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, sqlalchemy_integrity_error_handler)
```

## Usage in Routes
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/users/{user_id}")
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise UserNotFound(f"User {user_id} not found")
    return user

@router.post("/users/")
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing:
        raise DataAlreadyExists("A user with this email already exists")
    user = User(**payload.model_dump())
    db.add(user)
    db.commit()
    return user
```
