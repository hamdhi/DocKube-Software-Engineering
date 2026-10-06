r"""Chapter 29 - FastAPI and a real Python project structure (routers, services, repositories, schemas)."""

CHAPTER = r"""<h2>1. Why FastAPI</h2>

<table>
<tr><th>Property</th><th>What it means</th></tr>
<tr><td>Fast (ASGI)</td><td>Uvicorn + async - near Node/Go speed for I/O workloads</td></tr>
<tr><td>Typed</td><td>Pydantic models validate input and serialise output automatically</td></tr>
<tr><td>Documented</td><td>/docs (Swagger) and /redoc generated from your type hints - for free</td></tr>
<tr><td>Standards-based</td><td>OpenAPI, JSON Schema, OAuth2, HTTP standards</td></tr>
<tr><td>Async-native</td><td>async def endpoints run concurrently; sync endpoints get a thread pool</td></tr>
</table>

<pre>pip install fastapi uvicorn[standard] pydantic-settings sqlalchemy

# main.py
from fastapi import FastAPI
app = FastAPI(title="DocKube API", version="1.3.0")

@app.get("/health")
def health():
    return {"status": "ok"}

uvicorn main:app --reload                      # development
uvicorn main:app --host 0.0.0.0 --workers 4    # production
</pre>

<h2>2. Routes, Parameters, Validation</h2>

<pre>from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

class ItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    price: float = Field(gt=0)

class ItemOut(ItemIn):
    id: int

@app.post("/items", response_model=ItemOut, status_code=201)
async def create_item(body: ItemIn):          # body validated by Pydantic
    return {**body.model_dump(), "id": 1}

@app.get("/items/{item_id}")                  # path parameter
def get_item(item_id: int,                   # FastAPI converts and validates
             q: str | None = Query(None, max_length=20),
             verbose: bool = False):
    if item_id not in DB:
        raise HTTPException(404, detail="item not found")
    return DB[item_id]
</pre>

<table>
<tr><th>You declare</th><th>FastAPI does</th></tr>
<tr><td>path param typed int</td><td>Converts "abc" -&gt; 422 automatically, adds it to OpenAPI</td></tr>
<tr><td>body: ItemIn</td><td>Parses JSON, validates every field, returns 422 with exact errors</td></tr>
<tr><td>response_model=ItemOut</td><td>Filters leaked fields, serialises, documents the response</td></tr>
<tr><td>async def</td><td>Runs on the event loop - never block it</td></tr>
<tr><td>def (sync)</td><td>Runs in a threadpool - safe for blocking DB drivers</td></tr>
</table>
<h2>3. The Folder Structure - Python Terms</h2>

<p>Spring calls them controllers, services, DAOs/repositories and DTOs.
Python projects with FastAPI use the same layering under these names:</p>

<table>
<tr><th>Spring term</th><th>Python / FastAPI term</th><th>Its job</th></tr>
<tr><td>Controller</td><td><strong>Router</strong> (routers/)</td><td>HTTP only: parse request, call service, return response</td></tr>
<tr><td>Service</td><td><strong>Service</strong> (services/)</td><td>Business rules; no FastAPI imports here</td></tr>
<tr><td>DAO / Repository</td><td><strong>Repository</strong> (repositories/)</td><td>All SQL / ORM access; returns domain objects</td></tr>
<tr><td>DTO</td><td><strong>Schema</strong> (schemas/)</td><td>Pydantic models for request/response shapes</td></tr>
<tr><td>Entity</td><td><strong>Model</strong> (models/)</td><td>SQLAlchemy table mapping</td></tr>
<tr><td>Bean / DI container</td><td><strong>Depends()</strong> dependency injection</td><td>FastAPI builds and injects dependencies per request</td></tr>
<tr><td>application.yml</td><td><strong>.env + Settings</strong> (core/config.py)</td><td>Typed configuration</td></tr>
<tr><td>Interceptor / Filter</td><td><strong>Middleware</strong></td><td>Logging, request ids, CORS - runs around every request</td></tr>
<tr><td>@ControllerAdvice</td><td><strong>exception_handlers</strong></td><td>Central error -&gt; JSON mapping</td></tr>
</table>

<pre>app/
|-- main.py                 # app factory, middleware, exception handlers
|-- core/
|   |-- config.py           # Settings(BaseSettings) loaded from .env
|   |-- security.py         # password hashing, JWT create/verify
|   `-- logging.py          # structured logging setup
|-- db.py                   # engine, SessionLocal, Base, get_db()
|-- dependencies.py         # get_db, get_current_user - reusable Depends
|-- schemas/                # Pydantic DTOs (what the API speaks)
|   |-- item.py             # ItemIn, ItemOut, ItemUpdate
|   `-- user.py
|-- models/                 # SQLAlchemy tables (what the DB stores)
|   `-- item.py
|-- repositories/           # the ONLY place with SQL and queries
|   `-- item_repo.py
|-- services/               # business logic and transactions
|   `-- item_service.py
|-- routers/                # HTTP layer only
|   |-- items.py
|   `-- auth.py
|-- tests/
|   |-- conftest.py         # test app + throwaway database fixtures
|   `-- test_items.py
|-- .env.example
`-- requirements.txt
</pre>

<p><strong>Memory trick:</strong> a request flows <strong>router -&gt;
service -&gt; repository -&gt; database</strong>, and each layer only talks
to the next. If you ever import FastAPI inside a service or repository, the
layering has leaked.</p>
<h2>4. One Feature, All Layers</h2>

<pre># schemas/item.py - what crosses the wire
class ItemCreate(BaseModel):
    name: str = Field(min_length=1)
    price: float = Field(gt=0)

class ItemOut(ItemCreate):
    id: int
    owner_id: int
    model_config = {"from_attributes": True}    # ORM object -&gt; model

# repositories/item_repo.py - the only file that knows SQL
def create(db: Session, data: ItemCreate, owner_id: int):
    row = models.Item(**data.model_dump(), owner_id=owner_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

def get(db: Session, item_id: int):
    return db.get(models.Item, item_id)

# services/item_service.py - rules, not HTTP
class ItemService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: ItemCreate, owner_id: int):
        taken = (self.db.query(models.Item)
                    .filter_by(name=data.name, owner_id=owner_id).first())
        if taken:
            raise DomainError("you already have an item called that")
        return item_repo.create(self.db, data, owner_id)

# routers/items.py - HTTP only
router = APIRouter(prefix="/items", tags=["items"])

def get_service(db: Session = Depends(get_db),
                user = Depends(get_current_user)):
    return ItemService(db)                      # built per request

@router.post("", response_model=ItemOut, status_code=201)
def create(body: ItemCreate, svc = Depends(get_service)):
    try:
        return svc.create(body, user["sub"])
    except DomainError as exc:
        raise HTTPException(409, detail=str(exc))

# main.py - assemble the app
from routers import items, auth
app.include_router(items.router)
app.include_router(auth.router)
</pre>
<h2>5. Configuration, Middleware And Error Handling</h2>

<pre># core/config.py - typed settings, never os.environ scattered around
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    redis_url: str = "redis://localhost:6379/0"
    model_config = {"env_file": ".env"}

settings = Settings()          # app refuses to start with missing keys

# main.py - middleware wraps EVERY request (order matters: first added = outermost)
from fastapi import Request
import time, uuid, logging

@app.middleware("http")
async def request_context(request: Request, call_next):
    rid = request.headers.get("x-request-id", uuid.uuid4().hex[:12])
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["x-request-id"] = rid
    logging.info("%s %s %s %.1fms rid=%s", request.method,
                 request.url.path, response.status_code,
                 (time.perf_counter() - start) * 1000, rid)
    return response

@app.exception_handler(DomainError)
async def domain_errors(request: Request, exc: DomainError):
    # One JSON shape for every failure: {error: {code, message}}
    return JSONResponse(status_code=409,
                        content={"error": {"code": "conflict", "message": str(exc)}})

# CORS - exact origins, never *
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware,
                   allow_origins=["https://app.example.com"],
                   allow_credentials=True,
                   allow_methods=["GET", "POST"],
                   allow_headers=["authorization", "content-type"])
</pre>

<h2>6. Testing The App</h2>

<pre># tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import override_get_db

app.dependency_overrides[get_db] = override_get_db   # throwaway database

@pytest.fixture
def client():
    with TestClient(app) as c:                  # runs startup/shutdown hooks
        yield c

# tests/test_items.py
def test_create_and_read(client):
    r = client.post("/items", json={"name": "desk", "price": 120})
    assert r.status_code == 201
    item_id = r.json()["id"]
    assert client.get(f"/items/{item_id}").json()["name"] == "desk"

def test_rejects_bad_input(client):
    r = client.post("/items", json={"name": "", "price": -1})
    assert r.status_code == 422        # validation is FastAPI's job

# Run: pytest -q --cov=app
</pre>

<table>
<tr><th>Test type</th><th>Tool</th><th>Covers</th></tr>
<tr><td>Unit</td><td>pytest</td><td>Service and repository logic in isolation</td></tr>
<tr><td>Integration (API)</td><td>TestClient + real database</td><td>Routing, validation, persistence together</td></tr>
<tr><td>Contract</td><td>schemathesis (generated from /openapi.json)</td><td>Every endpoint against the documented schema</td></tr>
<tr><td>End-to-end</td><td>Playwright</td><td>Front end against the real stack</td></tr>
</table>

<h2>7. Deploying</h2>

<pre># Dockerfile (slim, non-root)
FROM python:3.12-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -r appuser &amp;&amp; chown -R appuser /srv
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Behind a proxy: uvicorn workers are the app servers; nginx or the cloud
# load balancer terminates TLS. Migrations run BEFORE the new pods start:
alembic upgrade head &amp;&amp; uvicorn app.main:app
</pre>

<h2>8. Learning vs Production</h2>

<table>
<tr><th>Aspect</th><th>While learning</th><th>In production</th></tr>
<tr><td>Structure</td><td>Everything in main.py</td><td>routers / services / repositories / schemas, one feature per folder</td></tr>
<tr><td>Config</td><td>Hard-coded strings</td><td>BaseSettings + .env, validated at boot, secrets from a manager</td></tr>
<tr><td>Errors</td><td>HTTPException sprinkled everywhere</td><td>Domain exceptions + one central handler with a stable JSON shape</td></tr>
<tr><td>Database</td><td>One global engine, sessions created by hand</td><td>get_db dependency, pooling, Alembic migrations, repository isolation</td></tr>
<tr><td>Docs</td><td>Hand-written</td><td>/docs is the contract, checked in CI with schemathesis</td></tr>
<tr><td>Process</td><td>--reload</td><td>Multiple uvicorn workers behind a proxy, graceful shutdown on SIGTERM</td></tr>
</table>

<h2>9. Key Takeaways</h2>
<ul>
<li>FastAPI turns type hints into validation, documentation and
serialisation - the schema IS the contract.</li>
<li>Python's names for the Spring layers: router (controller), service,
repository (DAO), schema (DTO), model (entity), Depends (DI), middleware
(interceptor).</li>
<li>Requests flow router -&gt; service -&gt; repository; each layer imports
only the next.</li>
<li>async endpoints must never block; sync endpoints get a threadpool for
free.</li>
<li>Centralise errors, type your settings, test with TestClient against a
throwaway database.</li>
</ul>

<p><strong>Exercise:</strong> scaffold the structure above with a single
Item resource and every layer filled in; add one test per layer and run
pytest -q --cov=app.</p>
"""