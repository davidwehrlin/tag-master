````markdown
# Implementation Plan: Disc Golf Tag League API

**Branch**: `001-tag-league-api` | **Date**: 2025-11-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-tag-league-api/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a FastAPI Python backend API for disc golf tag league tracking system. The system manages players, leagues, seasons, rounds, and a dynamic tag-based ranking system where positions are reassigned after every round. Core features include JWT authentication with role-based access control (Player, TagMaster, Assistant), physical check-in requirements, card-based score entry with peer confirmation, fraud prevention mechanisms, and comprehensive monitoring with zero PII logging. The API is stateless, containerized with Docker, and designed for horizontal scaling on ECS.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Framework**: FastAPI 0.104+ (async ASGI framework for REST APIs)  
**ORM**: SQLAlchemy 2.0+ (async support with asyncpg driver)  
**Data Validation**: Pydantic 2.0+ (request/response models, settings management)  
**Authentication**: OAuth2 with JWT tokens (python-jose for JWT, passlib with bcrypt for password hashing)  
**Storage**: PostgreSQL 15+ (relational database with JSONB support)  
**Testing**: pytest 7.4+ with pytest-asyncio, httpx for async client testing  
**Containerization**: Docker with multi-stage builds, docker-compose for local development  
**Target Platform**: Linux containers (AWS ECS compatible, stateless horizontal scaling)  
**Project Type**: Single backend API (RESTful with OpenAPI/Swagger documentation)  
**Performance Goals**: 
  - 500ms p95 response time for standard queries
  - 1000 concurrent users without degradation
  - Tag reassignment completes within 5 seconds for 100+ player seasons
**Constraints**: 
  - Stateless (no local file storage, all state in PostgreSQL)
  - Zero PII in logs (use anonymized IDs only)
  - 50 requests/minute rate limit per authenticated user
  - All queries use indexed columns for filtering
**Scale/Scope**: 
  - 10,000+ players across multiple leagues
  - 138 functional requirements
  - 13 database entities with complex relationships
  - 50+ API endpoints with CRUD operations

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ I. Specification-Driven Development
- Complete specification exists at `/specs/001-tag-league-api/spec.md`
- 138 functional requirements documented
- 5 user stories with acceptance scenarios
- 31 success criteria defined
- All requirements mapped to implementation

### ✅ II. User Story Independence  
- US1 (Authentication) - Standalone, foundational
- US2 (League/Season Mgmt) - Depends only on US1
- US3 (Round Recording) - Depends on US1, US2
- US4 (Tag Rankings) - Depends on US1, US2, US3
- US5 (RBAC) - Cross-cutting, testable independently
- Priority order (P1→P5) ensures incremental delivery
- US1 alone delivers viable authentication MVP

### ✅ III. Test-First Development
- Pytest framework specified for unit and integration tests
- Test structure will mirror source structure
- Contract tests for API endpoints
- Integration tests for database operations
- Unit tests for business logic (tag reassignment, eligibility)

### ✅ IV. Structured Planning & Research
- Phase 0 will resolve: Database schema design, JWT implementation patterns, rate limiting strategy, monitoring setup, Docker configuration
- All technical unknowns documented in research.md
- Architecture decisions will be documented with rationale

### ✅ V. Foundation-First Architecture
- Phase 2 Foundational tasks include:
  - Database models and migrations (SQLAlchemy)
  - Authentication system (OAuth2/JWT)
  - API structure (FastAPI app, routers, middleware)
  - Error handling (custom exceptions, handlers)
  - Rate limiting middleware
  - Logging infrastructure (structured, PII-free)
  - Health check endpoints
  - Docker containerization
- No user story implementation begins until foundation is complete

### ✅ VI. Code Quality & Security
- Pydantic for request validation prevents XSS/injection
- SQLAlchemy ORM with parameterized queries prevents SQL injection
- Passlib with bcrypt for secure password hashing
- JWT tokens with expiration
- Rate limiting to prevent brute force
- Input sanitization on all endpoints
- Comprehensive error handling without exposing sensitive data
- Code structure: maximum 3-level nesting, utility modules for shared logic
- OpenAPI documentation auto-generated

### ✅ VII. Performance Optimization
- Database indexes on all filterable columns (player_id, league_id, season_id, round_id, tag_number)
- Async SQLAlchemy with connection pooling
- Batch operations for tag reassignment (single transaction)
- No N+1 queries (use joins and eager loading)
- Tag reassignment algorithm: O(n log n) sorting, not nested loops
- Query plan analysis for complex queries (eligibility calculation, standings)
- Pagination on all list endpoints to prevent large result sets

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code

**Note**: All backend API code lives in `backend/` folder at repository root to separate from future frontend.

```text
backend/
├── alembic/                    # Database migrations
│   ├── versions/              # Migration scripts
│   └── env.py                 # Alembic configuration
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI application entry point
│   ├── config.py              # Pydantic settings (env vars)
│   ├── database.py            # SQLAlchemy async engine, session
│   ├── dependencies.py        # Dependency injection (auth, db session)
│   ├── models/                # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── base.py           # Base model with common fields
│   │   ├── player.py         # Player, Role entities
│   │   ├── league.py         # League, Season, LeagueAssistant
│   │   ├── round.py          # Round, Card, Participation
│   │   ├── bet.py            # Bet entity
│   │   └── tag.py            # Tag, TagHistory entities
│   ├── schemas/               # Pydantic request/response models
│   │   ├── __init__.py
│   │   ├── player.py
│   │   ├── league.py
│   │   ├── round.py
│   │   ├── bet.py
│   │   └── tag.py
│   ├── api/                   # API routers
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py       # Authentication endpoints
│   │   │   ├── players.py    # Player CRUD
│   │   │   ├── leagues.py    # League CRUD
│   │   │   ├── seasons.py    # Season CRUD
│   │   │   ├── rounds.py     # Round CRUD
│   │   │   ├── participations.py   # Participation operations
│   │   │   ├── cards.py      # Card management
│   │   │   ├── scores.py     # Score entry/confirmation
│   │   │   ├── tags.py       # Tag standings, history
│   │   │   ├── bets.py       # Bet tracking
│   │   │   ├── assistants.py # Assistant role management
│   │   │   └── health.py     # Health check, metrics
│   ├── services/              # Business logic
│   │   ├── __init__.py
│   │   ├── auth.py           # JWT creation, password hashing
│   │   ├── tag_assignment.py # Tag reassignment algorithm
│   │   ├── eligibility.py    # Eligibility calculation
│   │   ├── score_verification.py # Score confirmation logic
│   │   └── permissions.py    # RBAC logic
│   ├── middleware/            # FastAPI middleware
│   │   ├── __init__.py
│   │   ├── rate_limit.py     # Rate limiting
│   │   ├── logging.py        # Structured logging (PII-free)
│   │   ├── cors.py           # CORS configuration
│   │   └── error_handler.py  # Global exception handling
│   ├── utils/                 # Utility functions
│   │   ├── __init__.py
│   │   ├── pagination.py     # Pagination helpers
│   │   ├── sanitize.py       # PII sanitization
│   │   └── validators.py     # Custom validators
│   └── exceptions.py          # Custom exception classes
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Pytest fixtures
│   ├── contract/             # API contract tests
│   │   ├── test_auth.py
│   │   ├── test_players.py
│   │   ├── test_leagues.py
│   │   ├── test_rounds.py
│   │   └── test_tags.py
│   ├── integration/          # Database integration tests
│   │   ├── test_tag_reassignment.py
│   │   ├── test_eligibility.py
│   │   └── test_score_flow.py
│   └── unit/                 # Unit tests
│       ├── test_services/
│       │   ├── test_tag_assignment.py
│       │   └── test_permissions.py
│       └── test_utils/
├── Dockerfile                # Multi-stage Docker build
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variable template
├── alembic.ini              # Alembic configuration
└── pytest.ini               # Pytest configuration

# Repository root also contains:
docker-compose.yml           # Local development with PostgreSQL (references ./backend)
.env                        # Environment variables (gitignored)
.gitignore
README.md

specs/001-tag-league-api/    # Feature documentation
├── spec.md                  # Feature specification
├── plan.md                  # This file
├── research.md              # Phase 0 output
├── data-model.md            # Phase 1 output
├── quickstart.md            # Phase 1 output
├── contracts/               # Phase 1 output
│   └── openapi.yaml        # Generated OpenAPI spec
└── tasks.md                 # Phase 2 output (via /speckit.tasks)
```

**Structure Decision**: Single backend API project structure. Using FastAPI's recommended layout with clear separation of concerns: models (ORM), schemas (Pydantic), api (routers), services (business logic), middleware (cross-cutting concerns). Tests mirror the source structure with contract/integration/unit separation.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitutional violations. All principles satisfied.

---

## Phase 0: Research & Technical Decisions

**Objective**: Resolve all technical unknowns and document architecture decisions before design begins.

### Research Tasks

1. **Database Schema Design**
   - Research: SQLAlchemy 2.0 async patterns with FastAPI
   - Research: PostgreSQL index strategies for tag reassignment queries
   - Research: Soft delete patterns with SQLAlchemy (deleted_at column vs is_deleted flag)
   - Decision needed: Migration strategy (Alembic configuration)

2. **Authentication & Authorization**
   - Research: OAuth2 password flow implementation with FastAPI
   - Research: JWT token best practices (expiration, refresh strategy)
   - Research: Role-based access control patterns with FastAPI dependencies
   - Decision needed: Token storage approach (stateless JWT only vs refresh tokens)

3. **Rate Limiting**
   - Research: Rate limiting strategies for FastAPI (slowapi, custom middleware)
   - Decision needed: Storage backend for rate limit counters (Redis vs in-memory with distributed lock)

4. **Monitoring & Logging**
   - Research: Structured logging libraries (structlog vs python-json-logger)
   - Research: PII sanitization patterns for logs
   - Research: Prometheus metrics integration with FastAPI
   - Decision needed: Notification system for monitoring alerts (webhook implementation)

5. **Tag Reassignment Algorithm**
   - Research: Efficient sorting and ranking algorithms for O(n log n) performance
   - Research: PostgreSQL transaction isolation levels for concurrent tag updates
   - Decision needed: Locking strategy to prevent race conditions

6. **Containerization & Deployment**
   - Research: Multi-stage Docker builds for Python (optimization strategies)
   - Research: FastAPI graceful shutdown handling
   - Research: Database connection pooling for horizontal scaling
   - Decision needed: Health check endpoint implementation (liveness vs readiness)

7. **Testing Strategy**
   - Research: pytest-asyncio patterns for async FastAPI tests
   - Research: Database fixture strategies (test database vs in-memory)
   - Research: httpx async client for contract tests
   - Decision needed: Test isolation approach (rollback per test vs fresh database)

### Output: research.md

Document all research findings with:
- **Decision**: What was chosen
- **Rationale**: Why chosen (performance, maintainability, ecosystem fit)
- **Alternatives Considered**: What else was evaluated and why rejected
- **Implementation Notes**: Key patterns, gotchas, best practices

---

## Phase 1: Design & Contracts

**Prerequisites**: research.md complete with all decisions documented

### Design Tasks

1. **Data Model Design** (`data-model.md`)
   - Extract 13 entities from spec: Player, Role, League, Season, LeagueAssistant, Round, Card, Participation, Bet, Tag, TagHistory
   - Define fields, types, constraints for each entity
   - Document relationships (one-to-many, many-to-many)
   - Specify indexes for performance (player_id, league_id, season_id, tag_number, etc.)
   - Define validation rules from functional requirements
   - Document state transitions (pending → confirmed for scores, registered → completed/DNF for participations)

2. **API Contract Generation** (`contracts/openapi.yaml`)
   - Map 138 functional requirements to API endpoints
   - Group by resource (players, leagues, seasons, rounds, participations, cards, scores, tags, bets, assistants)
   - Define request/response schemas with Pydantic models
   - Document authentication requirements (Bearer token)
   - Specify query parameters for filtering, sorting, pagination
   - Define error responses (400, 401, 403, 404, 422, 429, 500)
   - Include rate limit headers

3. **Development Environment Setup** (`quickstart.md`)
   - Docker compose configuration (PostgreSQL, API service)
   - Environment variable documentation
   - Database migration commands (Alembic)
   - Local development workflow
   - Test execution instructions
   - API documentation access (Swagger UI at /docs)

4. **Agent Context Update**
   - Run `.specify/scripts/bash/update-agent-context.sh copilot`
   - Add technology stack to agent context:
     - FastAPI 0.104+
     - SQLAlchemy 2.0+ (async)
     - Pydantic 2.0+
     - PostgreSQL 15+
     - pytest 7.4+
     - python-jose (JWT)
     - passlib (bcrypt)
     - Docker

### Output Files
- `specs/001-tag-league-api/data-model.md`
- `specs/001-tag-league-api/contracts/openapi.yaml`
- `specs/001-tag-league-api/quickstart.md`
- Updated agent context file (`.github/.copilot-instructions.md` or similar)

---

## Phase 2: Task Breakdown

**Note**: Phase 2 (task generation) is executed via `/speckit.tasks` command, NOT by `/speckit.plan`.

The tasks.md file will break down implementation into:
- **Foundational Phase**: Database models, auth system, middleware, error handling
- **User Story Phases**: US1 (Auth), US2 (Leagues), US3 (Rounds), US4 (Tags), US5 (RBAC)
- **Polish Phase**: Performance optimization, monitoring setup, documentation

Tasks will follow format: `[T###] [P?] [Story] Description with file path`

---

## Next Steps

1. ✅ **Phase 0**: Generate `research.md` with all technical decisions
2. ⏳ **Phase 1**: Generate `data-model.md`, `contracts/`, `quickstart.md`
3. ⏳ **Phase 1**: Run agent context update script
4. ⏳ **Phase 2**: Run `/speckit.tasks` to generate task breakdown
5. ⏳ **Implementation**: Execute tasks following the constitution

````
