# Pytest Testing Complete Guide

## Install
```bash
pip install pytest pytest-asyncio httpx
```

## Test Configuration (pytest.ini / pyproject.toml)
```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
```

## Database Test Fixture (conftest.py)
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, get_db

# Use in-memory SQLite for tests (or a test database)
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
```

## Unit Test Example
```python
# tests/test_users.py
import pytest
from fastapi.testclient import TestClient

class TestUserEndpoints:

    def test_create_user(self, client: TestClient):
        response = client.post("/api/v1/auth/signup", json={
            "email": "test@example.com",
            "password": "securepassword123"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "hashed_password" not in data  # Never expose password

    def test_create_duplicate_user(self, client: TestClient):
        client.post("/api/v1/auth/signup", json={
            "email": "test@example.com",
            "password": "securepassword123"
        })
        response = client.post("/api/v1/auth/signup", json={
            "email": "test@example.com",
            "password": "different456"
        })
        assert response.status_code == 400

    def test_login_success(self, client: TestClient):
        client.post("/api/v1/auth/signup", json={
            "email": "test@example.com",
            "password": "securepassword123"
        })
        response = client.post("/api/v1/auth/login", data={
            "username": "test@example.com",
            "password": "securepassword123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_wrong_password(self, client: TestClient):
        client.post("/api/v1/auth/signup", json={
            "email": "test@example.com",
            "password": "securepassword123"
        })
        response = client.post("/api/v1/auth/login", data={
            "username": "test@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401

    def test_protected_route_no_token(self, client: TestClient):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_protected_route_with_token(self, client: TestClient):
        client.post("/api/v1/auth/signup", json={
            "email": "test@example.com",
            "password": "securepassword123"
        })
        login = client.post("/api/v1/auth/login", data={
            "username": "test@example.com",
            "password": "securepassword123"
        })
        token = login.json()["access_token"]
        response = client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"
```

## Test Types
### Smoke Test (Does the app start?)
```python
def test_app_starts(client):
    response = client.get("/docs")
    assert response.status_code == 200
```

### Regression Test (Did we break something?)
```python
def test_user_crud_flow(client):
    # Create
    r = client.post("/api/v1/auth/signup", json={"email": "a@b.com", "password": "pass12345678"})
    assert r.status_code == 201
    # Login
    r = client.post("/api/v1/auth/login", data={"username": "a@b.com", "password": "pass12345678"})
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # Read
    r = client.get("/api/v1/auth/me", headers=headers)
    assert r.status_code == 200
    # Logout
    r = client.post("/api/v1/auth/logout", headers=headers)
    assert r.status_code == 200
```

## Running Tests
```bash
pytest                          # Run all tests
pytest tests/test_users.py      # Run specific file
pytest -k "login"              # Run tests matching "login"
pytest -v                      # Verbose output
pytest --tb=short              # Short traceback
pytest -x                      # Stop on first failure
pytest --cov=app               # With coverage
```

## Marking Tests
```python
import pytest

@pytest.mark.slow
def test_expensive_operation():
    ...

@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    ...

# Run only fast tests: pytest -m "not slow"
```
