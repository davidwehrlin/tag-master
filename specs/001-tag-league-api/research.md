# Technical Research: Disc Golf Tag League API

**Feature**: 001-tag-league-api  
**Date**: 2025-11-09  
**Status**: Complete

This document captures all technical research and architecture decisions made during Phase 0 planning.

---

## 1. Database Schema Design with SQLAlchemy 2.0

### Decision
Use SQLAlchemy 2.0 async ORM with asyncpg driver, following the declarative base pattern with separate model files per domain.

### Rationale
- **Async Support**: SQLAlchemy 2.0 provides first-class async support with `AsyncSession` and `AsyncEngine`, essential for FastAPI's async request handlers
- **Type Safety**: 2.0 introduces improved typing support, catching errors at development time
- **Performance**: asyncpg is the fastest PostgreSQL driver for Python
- **Separation of Concerns**: Separate model files (player.py, league.py, round.py, tag.py) improve maintainability

### Alternatives Considered
- **SQLAlchemy 1.4 with greenlet**: Rejected due to inferior async support and performance
- **Raw asyncpg**: Rejected due to lack of ORM features, more boilerplate code
- **Tortoise ORM**: Rejected due to smaller ecosystem, less mature async support

### Implementation Notes
```python
# database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/tagmaster"

engine = create_async_engine(DATABASE_URL, echo=False, pool_size=20, max_overflow=0)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session_maker() as session:
        yield session
```

**Key Patterns**:
- Use `async with` for session management
- Set `expire_on_commit=False` to prevent lazy loading issues
- Configure connection pooling for horizontal scaling (20 connections per instance)
- Use `relationship()` with lazy="selectin" for predictable eager loading

### Soft Delete Pattern

**Decision**: Use `deleted_at` timestamp column (nullable) over boolean `is_deleted` flag.

**Rationale**:
- Preserves deletion timestamp for audit trails
- Allows querying "deleted between X and Y dates"
- More information-rich than boolean flag

**Implementation**:
```python
# models/base.py
class SoftDeleteMixin:
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    @property
    def is_deleted(self):
        return self.deleted_at is not None
```

**Query Pattern**:
```python
# Only return non-deleted records by default
stmt = select(Player).where(Player.deleted_at.is_(None))
```

### Index Strategy

**Decision**: Create indexes on all foreign keys and frequently filtered columns.

**Required Indexes**:
- Player: `email` (unique), `deleted_at`
- League: `organizer_id`, `visibility`, `deleted_at`
- Season: `league_id`, `start_date`, `end_date`
- Round: `season_id`, `date`, `deleted_at`
- Checkin: `player_id`, `round_id`, `card_id`, `status`
- Card: `round_id`, `creator_id`
- Tag: `player_id`, `season_id`, `tag_number` (composite unique)
- TagHistory: `player_id`, `season_id`, `round_id`, `assignment_date`
- LeagueAssistant: `player_id`, `league_id` (composite unique)

**Composite Indexes** (for common query patterns):
- `(season_id, tag_number)` on Tag table (for standings queries)
- `(player_id, season_id)` on TagHistory (for player tag history)
- `(round_id, player_id)` on Checkin (for attendance lookups)

---

## 2. Authentication & Authorization

### Decision
Implement OAuth2 password flow with stateless JWT tokens (no refresh tokens in MVP).

### Rationale
- **OAuth2 Password Flow**: Standard, well-documented pattern for first-party applications
- **Stateless JWT**: No database lookups for auth validation, scales horizontally
- **Simplicity**: No refresh token complexity in MVP (can add later)
- **FastAPI Integration**: Built-in `OAuth2PasswordBearer` dependency

### Alternatives Considered
- **Session-based Auth**: Rejected due to statefulness (violates containerization requirement)
- **JWT with Refresh Tokens**: Deferred to post-MVP (adds complexity)
- **OAuth2 Authorization Code Flow**: Rejected (requires third-party provider, overkill for MVP)

### Implementation Notes

**JWT Token Structure**:
```python
{
  "sub": "player_id",  # Subject (player UUID)
  "email": "user@example.com",
  "roles": ["Player", "TagMaster"],  # For RBAC
  "exp": 1699564800,  # Expiration timestamp (24 hours)
  "iat": 1699478400   # Issued at timestamp
}
```

**Password Hashing**:
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

**JWT Creation**:
```python
from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

**FastAPI Dependency**:
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_player(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Player:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        player_id = payload.get("sub")
        if not player_id:
            raise HTTPException(status_code=401)
    except JWTError:
        raise HTTPException(status_code=401)
    
    # Fetch player from database
    player = await db.get(Player, player_id)
    if not player or player.deleted_at:
        raise HTTPException(status_code=401)
    return player
```

**Role-Based Access Control (RBAC)**:
```python
def require_role(required_role: str):
    async def role_checker(current_player: Player = Depends(get_current_player)):
        if required_role not in current_player.roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_player
    return role_checker

# Usage in route
@router.post("/leagues")
async def create_league(
    league_data: LeagueCreate,
    current_player: Player = Depends(require_role("TagMaster"))
):
    pass
```

---

## 3. Rate Limiting

### Decision
Use custom middleware with in-memory token bucket algorithm (no Redis in MVP).

### Rationale
- **Simplicity**: No external dependencies for MVP
- **Sufficient for MVP**: In-memory rate limiting works for single-instance deployments
- **Per-User Limiting**: 50 requests/minute per authenticated user
- **Stateless Friendly**: Can add Redis later for multi-instance deployments

### Alternatives Considered
- **slowapi library**: Rejected due to lack of async support and per-user limiting
- **Redis-based**: Deferred to post-MVP (adds infrastructure complexity)
- **API Gateway rate limiting**: Deferred (assumes AWS API Gateway or similar)

### Implementation Notes

**Token Bucket Algorithm**:
```python
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request, HTTPException

class RateLimiter:
    def __init__(self, requests_per_minute: int = 50):
        self.requests_per_minute = requests_per_minute
        self.user_buckets = defaultdict(lambda: {"tokens": requests_per_minute, "last_update": datetime.utcnow()})
    
    async def check_rate_limit(self, user_id: str):
        bucket = self.user_buckets[user_id]
        now = datetime.utcnow()
        
        # Refill tokens based on time elapsed
        time_elapsed = (now - bucket["last_update"]).total_seconds()
        bucket["tokens"] = min(
            self.requests_per_minute,
            bucket["tokens"] + (time_elapsed / 60) * self.requests_per_minute
        )
        bucket["last_update"] = now
        
        # Check if tokens available
        if bucket["tokens"] < 1:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        bucket["tokens"] -= 1

rate_limiter = RateLimiter()

# Middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        # Extract user_id from JWT token
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token:
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_id = payload.get("sub")
                await rate_limiter.check_rate_limit(user_id)
            except:
                pass  # Let auth middleware handle invalid tokens
    
    response = await call_next(request)
    return response
```

**Future Enhancement** (Post-MVP with Redis):
```python
# Use Redis with sliding window algorithm
async def check_rate_limit_redis(user_id: str, redis: Redis):
    key = f"rate_limit:{user_id}"
    now = datetime.utcnow().timestamp()
    window_start = now - 60  # 60 seconds window
    
    # Remove old entries
    await redis.zremrangebyscore(key, 0, window_start)
    
    # Count recent requests
    count = await redis.zcard(key)
    if count >= 50:
        raise HTTPException(status_code=429)
    
    # Add current request
    await redis.zadd(key, {str(now): now})
    await redis.expire(key, 60)
```

---

## 4. Monitoring & Logging

### Decision
Use `structlog` for structured logging with custom PII sanitization processor.

### Rationale
- **Structured Logging**: JSON output for log aggregation (CloudWatch, ELK)
- **Context Propagation**: Request IDs automatically added to all log messages
- **PII Sanitization**: Custom processor ensures zero PII in logs
- **Performance**: Low overhead, async-friendly

### Alternatives Considered
- **python-json-logger**: Rejected due to less flexible configuration
- **Standard logging**: Rejected due to unstructured output
- **Custom logging**: Rejected due to maintenance burden

### Implementation Notes

**Structured Logging Setup**:
```python
import structlog
from structlog.processors import JSONRenderer

# PII fields to sanitize
PII_FIELDS = {"email", "password", "name", "ip_address", "location"}

def sanitize_pii(logger, method_name, event_dict):
    """Remove PII from log events"""
    for key in list(event_dict.keys()):
        if key in PII_FIELDS:
            event_dict[key] = "[REDACTED]"
    return event_dict

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        sanitize_pii,  # Custom PII sanitization
        JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

log = structlog.get_logger()
```

**Middleware for Request Logging**:
```python
import uuid
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="")

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    
    log.info(
        "request_started",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        # Note: NOT logging query params (may contain PII)
    )
    
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    log.info(
        "request_completed",
        request_id=request_id,
        status_code=response.status_code,
        duration_ms=int(duration * 1000)
    )
    
    return response
```

**Prometheus Metrics**:
```python
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response

# Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"]
)

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

**Monitoring Notifications** (Webhook):
```python
import httpx

async def send_alert(alert_type: str, message: str):
    """Send monitoring alert via webhook"""
    webhook_url = os.getenv("MONITORING_WEBHOOK_URL")
    if not webhook_url:
        return
    
    payload = {
        "alert_type": alert_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "service": "tagmaster-api",
        # NO PII: use service name, error codes, not user details
    }
    
    async with httpx.AsyncClient() as client:
        try:
            await client.post(webhook_url, json=payload, timeout=5)
        except Exception as e:
            log.error("alert_send_failed", error=str(e))
```

---

## 5. Tag Reassignment Algorithm

### Decision
Use O(n log n) sorting with single database transaction and optimistic locking.

### Rationale
- **Performance**: Sorting is O(n log n), acceptable for 100+ players
- **Correctness**: Single transaction ensures atomic updates
- **Concurrency**: Optimistic locking prevents race conditions
- **Simplicity**: No complex distributed locking required

### Alternatives Considered
- **Nested Loops**: Rejected due to O(n²) complexity
- **Distributed Locks**: Rejected as overkill for MVP (adds complexity)
- **Queue-based Processing**: Deferred to post-MVP (adds infrastructure)

### Implementation Notes

**Tag Reassignment Algorithm**:
```python
async def reassign_tags(season_id: str, round_id: str, db: AsyncSession):
    """
    Reassign tags after round completion.
    Complexity: O(n log n) due to sorting
    """
    # 1. Fetch all eligible players in season with current tags
    stmt = (
        select(Checkin, Player, Tag)
        .join(Player, Checkin.player_id == Player.id)
        .join(Tag, and_(Tag.player_id == Player.id, Tag.season_id == season_id))
        .where(
            Checkin.round_id == round_id,
            Checkin.status == "completed",  # Exclude DNF
            Player.deleted_at.is_(None)
        )
    )
    result = await db.execute(stmt)
    players_with_scores = result.all()
    
    # 2. Sort by score (ascending), then by previous tag number (ascending)
    # O(n log n) complexity
    sorted_players = sorted(
        players_with_scores,
        key=lambda x: (x.Checkin.score, x.Tag.tag_number)
    )
    
    # 3. Reassign tags in single transaction
    async with db.begin():
        for new_tag_number, (checkin, player, old_tag) in enumerate(sorted_players, start=1):
            if old_tag.tag_number != new_tag_number:
                # Update Tag table
                old_tag.tag_number = new_tag_number
                old_tag.assignment_date = datetime.utcnow()
                
                # Insert TagHistory record
                history = TagHistory(
                    tag_number=new_tag_number,
                    player_id=player.id,
                    season_id=season_id,
                    round_id=round_id,
                    assignment_date=datetime.utcnow()
                )
                db.add(history)
        
        await db.commit()
```

**Concurrency Control**:
```python
# Use SELECT FOR UPDATE to lock rows during tag reassignment
stmt = (
    select(Tag)
    .where(Tag.season_id == season_id)
    .with_for_update()  # Locks rows for update
)
```

**Eligibility Check** (Separate function, called before tag reassignment):
```python
async def check_eligibility(player_id: str, season_id: str, db: AsyncSession) -> bool:
    """
    Check if player meets eligibility requirements:
    - Minimum 3 completed rounds in league (season-independent)
    - Minimum 1 round in last 5 rounds of season
    """
    # Get league_id from season
    season = await db.get(Season, season_id)
    league_id = season.league_id
    
    # Count completed rounds in league (excluding DNF)
    league_rounds_stmt = (
        select(func.count(Checkin.id))
        .join(Round, Checkin.round_id == Round.id)
        .join(Season, Round.season_id == Season.id)
        .where(
            Checkin.player_id == player_id,
            Season.league_id == league_id,
            Checkin.status == "completed"
        )
    )
    league_rounds_count = await db.scalar(league_rounds_stmt)
    
    if league_rounds_count < 3:
        return False
    
    # Check 1 round in last 5 rounds of season
    last_5_rounds_stmt = (
        select(Round.id)
        .where(Round.season_id == season_id)
        .order_by(Round.date.desc())
        .limit(5)
    )
    last_5_rounds = await db.execute(last_5_rounds_stmt)
    last_5_round_ids = [r.id for r in last_5_rounds.scalars()]
    
    recent_participation_stmt = (
        select(func.count(Checkin.id))
        .where(
            Checkin.player_id == player_id,
            Checkin.round_id.in_(last_5_round_ids),
            Checkin.status == "completed"
        )
    )
    recent_count = await db.scalar(recent_participation_stmt)
    
    return recent_count >= 1
```

---

## 6. Containerization & Deployment

### Decision
Multi-stage Docker build with Alpine base, docker-compose for local development.

### Rationale
- **Small Image Size**: Alpine Linux reduces image size
- **Security**: Fewer packages, smaller attack surface
- **Fast Builds**: Multi-stage build caches dependencies
- **Local Dev**: docker-compose includes PostgreSQL for easy setup

### Alternatives Considered
- **Ubuntu/Debian Base**: Rejected due to larger image size (10x larger)
- **Docker Swarm**: Rejected in favor of AWS ECS (per requirements)
- **Kubernetes**: Deferred to post-MVP (overkill for MVP)

### Implementation Notes

**Multi-Stage Dockerfile**:
```dockerfile
# Stage 1: Build dependencies
FROM python:3.11-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache gcc musl-dev postgresql-dev

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-alpine

WORKDIR /app

# Install runtime dependencies only
RUN apk add --no-cache postgresql-libs

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY ./backend/app /app/app
COPY ./backend/alembic /app/alembic
COPY ./backend/alembic.ini /app/

# Create non-root user
RUN adduser -D appuser
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml** (Local Development):
```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: tagmaster
      POSTGRES_PASSWORD: dev_password
      POSTGRES_DB: tagmaster_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U tagmaster"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://tagmaster:dev_password@db:5432/tagmaster_dev
      JWT_SECRET_KEY: dev_secret_key_change_in_production
      CORS_ORIGINS: "http://localhost:3000,http://localhost:8080"
    depends_on:
      db:
        condition: service_healthy
    command: >
      sh -c "
        alembic upgrade head &&
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
      "

volumes:
  postgres_data:
```

**Graceful Shutdown**:
```python
# main.py
import signal
import asyncio

shutdown_event = asyncio.Event()

def handle_shutdown(signum, frame):
    log.info("shutdown_signal_received", signal=signum)
    shutdown_event.set()

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

@app.on_event("shutdown")
async def shutdown():
    log.info("application_shutdown_started")
    # Wait for in-flight requests (FastAPI handles this)
    await asyncio.sleep(2)
    # Close database connections
    await engine.dispose()
    log.info("application_shutdown_completed")
```

**Health Check Endpoint**:
```python
@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint for container orchestration.
    Returns 200 if API and database are healthy.
    """
    try:
        # Check database connectivity
        await db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        log.error("health_check_failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unhealthy")
```

---

## 7. Testing Strategy

### Decision
Use pytest with pytest-asyncio for async tests, separate test database with rollback per test.

### Rationale
- **Async Support**: pytest-asyncio enables testing async FastAPI endpoints
- **Isolation**: Rollback per test ensures clean state
- **Realistic**: Test database matches production schema
- **Speed**: Transactions are fast, no need for in-memory DB

### Alternatives Considered
- **In-Memory SQLite**: Rejected due to PostgreSQL-specific features (JSONB, array types)
- **Shared Test DB**: Rejected due to test pollution
- **Mocking DB**: Rejected for integration tests (mocks don't catch real DB issues)

### Implementation Notes

**Pytest Configuration** (`pytest.ini`):
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --cov=app
    --cov-report=html
    --cov-report=term-missing
markers =
    unit: Unit tests (no external dependencies)
    integration: Integration tests (database required)
    contract: API contract tests (full HTTP stack)
```

**Test Fixtures** (`conftest.py`):
```python
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient
from app.main import app
from app.database import get_db
from app.models.base import Base

TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/tagmaster_test"

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
async def db_session(test_engine):
    """Create database session with rollback per test"""
    connection = await test_engine.connect()
    transaction = await connection.begin()
    
    async_session_maker = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
    
    await transaction.rollback()
    await connection.close()

@pytest.fixture
async def client(db_session):
    """Create test client with overridden database dependency"""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()
```

**Example Contract Test**:
```python
@pytest.mark.contract
async def test_create_player(client: AsyncClient):
    """Test player registration endpoint"""
    response = await client.post(
        "/api/v1/players",
        json={
            "email": "test@example.com",
            "password": "SecurePass123",
            "name": "Test Player"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "password" not in data  # Password should not be returned
    assert "id" in data
```

**Example Integration Test**:
```python
@pytest.mark.integration
async def test_tag_reassignment(db_session: AsyncSession):
    """Test tag reassignment algorithm"""
    # Setup: Create season, players, round, check-ins
    season = Season(id=uuid4(), name="Test Season", league_id=league.id)
    db_session.add(season)
    
    # Add 3 players with tags
    players = [
        Player(id=uuid4(), email=f"player{i}@test.com", name=f"Player {i}")
        for i in range(3)
    ]
    for i, player in enumerate(players):
        db_session.add(player)
        tag = Tag(player_id=player.id, season_id=season.id, tag_number=i+1)
        db_session.add(tag)
    
    # Create round with check-ins and scores
    round_obj = Round(id=uuid4(), season_id=season.id, date=datetime.utcnow())
    db_session.add(round_obj)
    
    scores = [65, 70, 60]  # Player 2 has best score (60)
    for player, score in zip(players, scores):
        checkin = Checkin(
            player_id=player.id,
            round_id=round_obj.id,
            score=score,
            status="completed"
        )
        db_session.add(checkin)
    
    await db_session.commit()
    
    # Execute tag reassignment
    await reassign_tags(season.id, round_obj.id, db_session)
    
    # Verify: Player 2 (score 60) should now have Tag #1
    stmt = select(Tag).where(Tag.player_id == players[2].id)
    tag = await db_session.scalar(stmt)
    assert tag.tag_number == 1
```

**Example Unit Test**:
```python
@pytest.mark.unit
def test_password_hashing():
    """Test password hashing and verification"""
    plain_password = "TestPassword123"
    hashed = hash_password(plain_password)
    
    # Verify hashed password is different from plain
    assert hashed != plain_password
    
    # Verify correct password validates
    assert verify_password(plain_password, hashed)
    
    # Verify incorrect password fails
    assert not verify_password("WrongPassword", hashed)
```

---

## Summary of Key Decisions

| Area | Decision | Key Benefits |
|------|----------|--------------|
| **Database** | SQLAlchemy 2.0 async + asyncpg + PostgreSQL 15 | Performance, type safety, async support |
| **API Framework** | FastAPI with Pydantic 2.0 | Auto validation, OpenAPI docs, async |
| **Authentication** | OAuth2 password flow + stateless JWT | Standard pattern, horizontal scaling |
| **Authorization** | Role-based (Player/TagMaster/Assistant) | Granular permissions, simple model |
| **Rate Limiting** | In-memory token bucket (50 req/min) | Simple, stateless-friendly |
| **Logging** | structlog with PII sanitization | Structured JSON, zero PII |
| **Monitoring** | Prometheus metrics + webhook alerts | Standard observability stack |
| **Tag Algorithm** | O(n log n) sort + single transaction | Fast, correct, scalable |
| **Containerization** | Multi-stage Docker + docker-compose | Small images, easy local dev |
| **Testing** | pytest + async + test DB rollback | Isolated, realistic, fast |

---

## Next Steps

All technical unknowns are resolved. Proceeding to Phase 1:
- ✅ **Phase 0 Complete**: All research documented
- ⏳ **Phase 1**: Generate data-model.md, contracts/, quickstart.md
- ⏳ **Phase 1**: Update agent context with technology stack
- ⏳ **Phase 2**: Generate tasks.md via `/speckit.tasks`
