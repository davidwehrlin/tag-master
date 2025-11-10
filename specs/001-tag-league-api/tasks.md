# Tasks: Disc Golf Tag League API

**Input**: Design documents from `/specs/001-tag-league-api/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/openapi.yaml  
**Tests**: Not explicitly requested in specification - test tasks omitted per constitution  

**Project Structure**: All backend API code will be located in `backend/` folder at repository root to maintain separation from future frontend implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create backend project structure per plan.md (backend/app/, backend/tests/, alembic/)
- [X] T002 Initialize Python project with requirements.txt (FastAPI 0.104+, SQLAlchemy 2.0+, Pydantic 2.0+, python-jose, passlib, pytest 7.4+, pytest-asyncio, httpx, alembic, asyncpg, structlog)
- [X] T003 [P] Create Docker multi-stage build in backend/Dockerfile per research.md (builder stage with gcc/musl-dev, runtime stage with Alpine)
- [X] T004 [P] Create docker-compose.yml with PostgreSQL 15+ and FastAPI services per quickstart.md
- [X] T005 [P] Configure pytest with pytest.ini (asyncio_mode=auto, markers for contract/integration/unit)
- [X] T006 [P] Create .env.example with all environment variables per quickstart.md (DATABASE_URL, JWT_SECRET_KEY, CORS_ORIGINS, RATE_LIMIT_PER_MINUTE, etc.)
- [X] T007 [P] Configure Alembic in alembic.ini and alembic/env.py for async SQLAlchemy support

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database Foundation

- [X] T008 Create base models in backend/app/models/base.py (BaseModel with UUID id, created_at, updated_at; SoftDeleteMixin with deleted_at)
- [X] T009 Configure async SQLAlchemy engine and session in backend/app/database.py (asyncpg driver, connection pooling 20 connections per research.md)
- [X] T010 Create Alembic migration for players table in alembic/versions/001_create_players.py (email unique index, deleted_at index per data-model.md)
- [X] T011 Create Alembic migration for leagues table in alembic/versions/002_create_leagues.py (organizer_id index, visibility index, deleted_at index)
- [X] T012 Create Alembic migration for seasons table in alembic/versions/003_create_seasons.py (league_id index, start_date/end_date composite index)
- [X] T013 Create Alembic migration for league_assistants table in alembic/versions/004_create_league_assistants.py (player_id + league_id unique constraint)
- [X] T014 Create Alembic migration for rounds table in alembic/versions/005_create_rounds.py (season_id index, date index, deleted_at index)
- [X] T015 Create Alembic migration for cards table in alembic/versions/006_create_cards.py (round_id index, creator_id index)
- [X] T016 Create Alembic migration for participations table in alembic/versions/007_create_participations.py (player_id + round_id unique constraint, status index, card_id index)
- [X] T017 Create Alembic migration for bets table in alembic/versions/008_create_bets.py (player_id index, round_id index, bet_type index)
- [X] T018 Create Alembic migration for tags table in alembic/versions/009_create_tags.py (player_id + season_id unique, season_id + tag_number unique, composite index)
- [X] T019 Create Alembic migration for tag_history table in alembic/versions/010_create_tag_history.py (player_id + season_id composite index, assignment_date index)

### Authentication & Authorization Foundation

- [X] T020 Implement password hashing utilities in backend/app/services/auth.py (bcrypt via passlib per research.md)
- [X] T021 Implement JWT token creation and verification in backend/app/services/auth.py (HS256 algorithm, 24hr expiration per research.md)
- [X] T022 Create OAuth2 password bearer dependency in backend/app/dependencies.py (get_current_user extracts JWT token)
- [X] T023 Create RBAC permission checking utilities in backend/app/services/permissions.py (can_manage_league, can_manage_round, is_tag_master_or_assistant)

### Core Infrastructure

- [X] T024 Create Pydantic settings configuration in backend/app/config.py (BaseSettings with DATABASE_URL, JWT_SECRET_KEY, CORS_ORIGINS, RATE_LIMIT_PER_MINUTE, etc.)
- [X] T025 Implement rate limiting middleware in backend/app/middleware/rate_limit.py (in-memory token bucket 50 req/min per user per research.md)
- [X] T026 [P] Implement structured logging with PII sanitization in backend/app/middleware/logging.py (structlog with custom processor to redact email, password, name, ip_address per research.md)
- [X] T027 [P] Configure CORS middleware in backend/app/middleware/cors.py (CORSMiddleware with origins from settings)
- [X] T028 [P] Implement global error handler in backend/app/middleware/error_handler.py (catch all exceptions, return ErrorResponse schema, log without PII)
- [X] T029 Create custom exception classes in backend/app/exceptions.py (AuthenticationError, AuthorizationError, NotFoundError, ValidationError, RateLimitError)
- [X] T030 Create pagination utilities in backend/app/utils/pagination.py (paginate function with total, page, size, pages metadata)
- [X] T031 Create FastAPI application in backend/app/main.py (include all middleware, routers, startup/shutdown events for database)
- [X] T032 Create health check endpoint in backend/app/api/v1/health.py (GET /health returns 200 with database status, GET /metrics returns Prometheus format per research.md)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Player Registration & Authentication (Priority: P1) 🎯 MVP

**Goal**: Players can create accounts, log in, and manage their profiles

**Independent Test**: Create new player account, login to receive JWT token, update profile, verify changes persist

### Models for User Story 1

- [ ] T033 [P] [US1] Create Player model in backend/app/models/player.py (PlayerRole enum, Player class with email, password_hash, name, bio, roles[], email_verified, soft delete per data-model.md)
- [ ] T034 [P] [US1] Create Player Pydantic schemas in backend/app/schemas/player.py (PlayerRegister, PlayerLogin, TokenResponse, PlayerResponse, PlayerUpdate per contracts/openapi.yaml)

### Implementation for User Story 1

- [ ] T035 [US1] Implement authentication endpoints in backend/app/api/v1/auth.py (POST /auth/register, POST /auth/login per contracts/openapi.yaml)
- [ ] T036 [US1] Implement player profile endpoints in backend/app/api/v1/players.py (GET /players/me, PUT /players/me, DELETE /players/me with soft delete, GET /players with pagination, GET /players/{id})
- [ ] T037 [US1] Add email validation (valid format, unique across non-deleted players) in backend/app/schemas/player.py
- [ ] T038 [US1] Add password validation (min 8 chars, uppercase, lowercase, number) in backend/app/schemas/player.py
- [ ] T039 [US1] Implement registration logic (hash password, create player with Player role, generate JWT) in backend/app/api/v1/auth.py
- [ ] T040 [US1] Implement login logic (verify password, generate JWT with player_id, email, roles in payload) in backend/app/api/v1/auth.py
- [ ] T041 [US1] Add request ID correlation to logging for auth operations in backend/app/middleware/logging.py

**Checkpoint**: At this point, User Story 1 should be fully functional - players can register, login, view/update profiles

---

## Phase 4: User Story 2 - League Creation & Season Management (Priority: P2)

**Goal**: League organizers can create leagues, define seasons, and manage registration. Creating league auto-assigns TagMaster role.

**Independent Test**: Player creates first league (becomes TagMaster), adds season with dates, another player registers for season and receives tag

### Models for User Story 2

- [ ] T042 [P] [US2] Create League model in backend/app/models/league.py (LeagueVisibility enum, League class with name, description, rules, visibility, organizer_id, soft delete per data-model.md)
- [ ] T043 [P] [US2] Create Season model in backend/app/models/league.py (Season class with name, league_id, start_date, end_date, registration dates per data-model.md)
- [ ] T044 [P] [US2] Create LeagueAssistant model in backend/app/models/league.py (LeagueAssistant class with player_id + league_id unique constraint per data-model.md)
- [ ] T045 [P] [US2] Create Tag model in backend/app/models/tag.py (Tag class with player_id + season_id unique, season_id + tag_number unique per data-model.md)
- [ ] T046 [P] [US2] Create League Pydantic schemas in backend/app/schemas/league.py (LeagueCreate, LeagueResponse, LeagueUpdate, SeasonCreate, SeasonResponse per contracts/openapi.yaml)

### Implementation for User Story 2

- [ ] T047 [US2] Implement league endpoints in backend/app/api/v1/leagues.py (GET /leagues with pagination/visibility filter, POST /leagues auto-assigns TagMaster role, GET /leagues/{id}, PUT /leagues/{id}, DELETE /leagues/{id} soft delete per contracts/openapi.yaml)
- [ ] T048 [US2] Implement season endpoints in backend/app/api/v1/seasons.py (GET /seasons with pagination/filters, POST /seasons, GET /seasons/{id} per contracts/openapi.yaml)
- [ ] T049 [US2] Implement season registration endpoint in backend/app/api/v1/seasons.py (POST /seasons/{id}/register assigns next available tag number first-come-first-served per contracts/openapi.yaml)
- [ ] T050 [US2] Add TagMaster role assignment logic in backend/app/api/v1/leagues.py (append "TagMaster" to player.roles when creating first league)
- [ ] T051 [US2] Add league permission checks in backend/app/api/v1/leagues.py (organizer_id == current_player_id OR LeagueAssistant exists for updates/deletes per research.md)
- [ ] T052 [US2] Add season date validation (end_date after start_date, registration dates logic) in backend/app/schemas/league.py
- [ ] T053 [US2] Implement tag assignment service in backend/app/services/tag_assignment.py (assign_initial_tag function: finds max tag_number in season, increments by 1, creates Tag record)
- [ ] T054 [US2] Add soft delete validation (cannot delete league with active seasons with rounds) in backend/app/api/v1/leagues.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - players can register/login AND create leagues/seasons with tag assignment

---

## Phase 5: User Story 3 - Round Recording & Attendance (Priority: P3)

**Goal**: Players and organizers record rounds, track attendance via participations, enter scores with peer confirmation

**Independent Test**: Create round, players register online, TagMaster checks in physically, players create cards, enter scores, confirm scores, verify all data persists

### Models for User Story 3

- [ ] T055 [P] [US3] Create Round model in backend/app/models/round.py (Round class with season_id, creator_id, date, course_name, location, start_time, soft delete per data-model.md)
- [ ] T056 [P] [US3] Create Card model in backend/app/models/round.py (Card class with round_id, creator_id per data-model.md)
- [ ] T057 [P] [US3] Create Participation model in backend/app/models/round.py (ParticipationStatus enum, Participation class with player_id + round_id unique, card_id, status, timestamps, score fields per data-model.md)
- [ ] T058 [P] [US3] Create Bet model in backend/app/models/bet.py (BetType enum, Bet class with player_id, round_id, bet_type, amount, description per data-model.md)
- [ ] T059 [P] [US3] Create Round Pydantic schemas in backend/app/schemas/round.py (RoundCreate, RoundResponse, ParticipationCreate, PhysicalParticipation, ParticipationResponse, CardCreate, CardResponse, ScoreEntry, ScoreConfirmation per contracts/openapi.yaml)
- [ ] T060 [P] [US3] Create Bet Pydantic schemas in backend/app/schemas/bet.py (BetCreate, BetResponse per contracts/openapi.yaml)

### Implementation for User Story 3

- [ ] T061 [US3] Implement round endpoints in backend/app/api/v1/rounds.py (GET /rounds with pagination/filters, POST /rounds TagMaster/Assistant only, GET /rounds/{id}, DELETE /rounds/{id} soft delete per contracts/openapi.yaml)
- [ ] T062 [US3] Implement participation endpoints in backend/app/api/v1/participations.py (GET /rounds/{id}/participations with status filter, POST /rounds/{id}/participations for online registration, POST /rounds/{id}/participations/physical TagMaster/Assistant only, POST /participations/{id}/dnf per contracts/openapi.yaml)
- [ ] T063 [US3] Implement card endpoints in backend/app/api/v1/cards.py (POST /cards with 3-6 checked-in players, GET /cards/{id} per contracts/openapi.yaml)
- [ ] T064 [US3] Implement score endpoints in backend/app/api/v1/scores.py (POST /cards/{id}/scores card creator only, POST /cards/{id}/scores/confirm non-creator only per contracts/openapi.yaml)
- [ ] T065 [US3] Implement bet endpoints in backend/app/api/v1/bets.py (GET /rounds/{id}/bets with bet_type filter per contracts/openapi.yaml)
- [ ] T066 [US3] Add round permission checks (creator must be TagMaster or Assistant for league) in backend/app/api/v1/rounds.py
- [ ] T067 [US3] Add participation validation (cannot register twice for same round, physical check-in updates status and timestamp) in backend/app/api/v1/participations.py
- [ ] T068 [US3] Add card validation (3-6 players minimum/maximum, all players must have status=checked_in, each player only on one card per round) in backend/app/api/v1/cards.py
- [ ] T069 [US3] Add score validation (can only enter score if status=checked_in, score_entered_by_id must be card creator) in backend/app/api/v1/scores.py
- [ ] T070 [US3] Add score confirmation validation (cannot confirm own score, must be different card member, updates status to completed) in backend/app/api/v1/scores.py
- [ ] T071 [US3] Add DNF logic (marks participation status=dnf, final state, excluded from tag reassignment) in backend/app/api/v1/participations.py
- [ ] T072 [US3] Add bet validation (amount must be positive, player must be checked in, recorded during physical participation) in backend/app/api/v1/participations.py

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently - complete round workflow with attendance, cards, scores, and confirmation

---

## Phase 6: User Story 4 - Tag-Based Rankings & Statistics (Priority: P4)

**Goal**: View current tag holders, tag history, and dynamic tag reassignment after each round based on performance

**Independent Test**: View season tag standings, complete round with confirmed scores, verify tags reassigned (best score gets Tag #1), view tag history showing progression

### Models for User Story 4

- [ ] T073 [P] [US4] Create TagHistory model in backend/app/models/tag.py (TagHistory class with tag_number, player_id, season_id, round_id, assignment_date, append-only per data-model.md)
- [ ] T074 [P] [US4] Create Tag Pydantic schemas in backend/app/schemas/tag.py (TagResponse with is_eligible field, TagHistoryResponse per contracts/openapi.yaml)

### Implementation for User Story 4

- [ ] T075 [US4] Implement tag standings endpoint in backend/app/api/v1/tags.py (GET /seasons/{id}/tags sorted by tag_number with eligible_only filter per contracts/openapi.yaml)
- [ ] T076 [US4] Implement tag history endpoint in backend/app/api/v1/tags.py (GET /players/{id}/tags/history with season filter per contracts/openapi.yaml)
- [ ] T077 [US4] Implement eligibility calculation service in backend/app/services/eligibility.py (check_eligibility function: minimum 3 completed rounds in league season-independent, 1 round in last 5 rounds of season, exclude DNF per research.md)
- [ ] T078 [US4] Implement tag reassignment algorithm in backend/app/services/tag_assignment.py (reassign_tags_after_round function: O(n log n) sorting by score then previous tag_number, single transaction with SELECT FOR UPDATE per research.md)
- [ ] T079 [US4] Add tag reassignment trigger in backend/app/api/v1/scores.py (call reassign_tags_after_round when all scores confirmed for round, only reassign participating players excluding DNF)
- [ ] T080 [US4] Add TagHistory record creation in backend/app/services/tag_assignment.py (create history entry on initial tag assignment and after each reassignment with round_id)
- [ ] T081 [US4] Add tie-breaking logic in backend/app/services/tag_assignment.py (player with lower tag_number before round keeps better tag on tie)
- [ ] T082 [US4] Add eligibility indicator to tag standings response in backend/app/api/v1/tags.py (call check_eligibility for each player, add is_eligible boolean to TagResponse)
- [ ] T083 [US4] Add validation for end-of-season eligibility display (apply eligibility rules only to standings display, not round-by-round reassignment per spec.md clarification)

**Checkpoint**: At this point, User Stories 1-4 should all work independently - complete tag lifecycle with reassignment and eligibility tracking

---

## Phase 7: User Story 5 - Role-Based Access Control (Priority: P5)

**Goal**: Enforce role-based permissions ensuring players can only modify own data while TagMasters/Assistants can manage leagues

**Independent Test**: Attempt various operations as different role types (Player, TagMaster, Assistant) and verify proper authorization

### Models for User Story 5

- [ ] T084 [P] [US5] Create Assistant Pydantic schemas in backend/app/schemas/assistant.py (AssistantAssign, AssistantResponse per contracts/openapi.yaml)

### Implementation for User Story 5

- [ ] T085 [US5] Implement assistant management endpoints in backend/app/api/v1/assistants.py (GET /leagues/{id}/assistants, POST /leagues/{id}/assistants TagMaster only, DELETE /leagues/{id}/assistants/{player_id} TagMaster only per contracts/openapi.yaml)
- [ ] T086 [US5] Add assistant assignment logic in backend/app/api/v1/assistants.py (create LeagueAssistant record, assigner must be TagMaster or league organizer)
- [ ] T087 [US5] Add assistant revocation logic in backend/app/api/v1/assistants.py (delete LeagueAssistant record, only TagMaster can revoke)
- [ ] T088 [US5] Add league-specific assistant permission checks in backend/app/services/permissions.py (can_manage_league checks organizer_id OR LeagueAssistant exists for player+league)
- [ ] T089 [US5] Add player profile permission checks in backend/app/api/v1/players.py (can only update/delete own profile except soft delete check)
- [ ] T090 [US5] Add round creation permission checks in backend/app/api/v1/rounds.py (creator must be TagMaster or Assistant for the league)
- [ ] T091 [US5] Add physical participation permission checks in backend/app/api/v1/participations.py (only TagMaster or Assistant can perform physical check-in)
- [ ] T092 [US5] Add score entry permission checks in backend/app/api/v1/scores.py (only card creator can enter scores)
- [ ] T093 [US5] Add score confirmation permission checks in backend/app/api/v1/scores.py (only non-creator card members can confirm)
- [ ] T094 [US5] Add DNF marking permission checks in backend/app/api/v1/participations.py (card creator or TagMaster/Assistant can mark DNF)
- [ ] T095 [US5] Add public league read access (any authenticated user can view public leagues) in backend/app/api/v1/leagues.py
- [ ] T096 [US5] Add cascade delete for LeagueAssistant when league deleted in backend/app/models/league.py (relationship cascade configuration)

**Checkpoint**: All user stories should now be independently functional with proper role-based access control across all operations

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T097 [P] Add Prometheus metrics collection in backend/app/api/v1/health.py (http_requests_total, http_request_duration_seconds, error rates per research.md)
- [ ] T098 [P] Add webhook alerts for monitoring thresholds in backend/app/middleware/logging.py (error rate > 5%, p95 latency > 500ms per research.md)
- [ ] T099 [P] Add comprehensive input validation across all endpoints (sanitize strings, validate UUIDs, check date ranges)
- [ ] T100 [P] Add pagination to all list endpoints (leagues, seasons, rounds, tags, participations per contracts/openapi.yaml)
- [ ] T101 [P] Optimize database queries with eager loading in backend/app/api/v1/ (use selectin loading for relationships to avoid N+1 queries per research.md)
- [ ] T102 [P] Add database query plan analysis for complex queries in backend/app/services/ (eligibility calculation, tag standings)
- [ ] T103 [P] Add comprehensive error messages without exposing sensitive data in backend/app/exceptions.py
- [ ] T104 [P] Update quickstart.md with complete API usage examples (11 curl commands covering full workflow)
- [ ] T105 [P] Generate OpenAPI documentation in backend/app/main.py (FastAPI auto-generates at /docs and /redoc)
- [ ] T106 [P] Add health check validation (database connectivity check with timeout) in backend/app/api/v1/health.py
- [ ] T107 [P] Add graceful shutdown handling in backend/app/main.py (handle SIGTERM/SIGINT, 2 sec delay for in-flight requests per research.md)
- [ ] T108 Run quickstart.md validation (docker-compose up, run migrations, test all 11 API examples, verify health endpoint)
- [ ] T109 Add rate limit headers to all responses in backend/app/middleware/rate_limit.py (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)
- [ ] T110 Add soft delete filtering to all queries in backend/app/api/v1/ (exclude deleted_at != null for players and rounds)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User Story 2 integrates with User Story 1 (needs authenticated players)
  - User Story 3 integrates with User Story 1 & 2 (needs authenticated players and leagues/seasons)
  - User Story 4 integrates with User Story 3 (needs rounds and scores)
  - User Story 5 is cross-cutting (adds permissions to all stories)
  - Stories can proceed in parallel if staffed, or sequentially in priority order (P1 → P2 → P3 → P4 → P5)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories ✅ FULLY INDEPENDENT
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires authenticated players from US1 for league creation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires authenticated players (US1) and leagues/seasons (US2) for round creation
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Requires rounds and scores from US3 for tag reassignment
- **User Story 5 (P5)**: Can start after Foundational (Phase 2) - Cross-cutting permissions affect all stories but can be tested independently

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1 (Setup)**: All tasks marked [P] can run in parallel (T003, T004, T005, T006, T007)
- **Phase 2 (Foundational)**: All tasks marked [P] can run in parallel within categories:
  - Migrations: T010-T019 can run sequentially (order matters for foreign keys)
  - Infrastructure: T026, T027, T028 can run in parallel (different middleware files)
- **User Story phases**: All models marked [P] within a story can run in parallel
- **Different user stories**: Can be worked on in parallel by different team members after Phase 2 completes

---

## Parallel Example: User Story 1

```bash
# Launch both models for User Story 1 together:
Task T033: "Create Player model in backend/app/models/player.py"
Task T034: "Create Player Pydantic schemas in backend/app/schemas/player.py"

# These run in parallel because they're in different files with no dependencies
```

## Parallel Example: User Story 2

```bash
# Launch all models for User Story 2 together:
Task T042: "Create League model in backend/app/models/league.py"
Task T043: "Create Season model in backend/app/models/league.py" (same file as T042, cannot parallel)
Task T044: "Create LeagueAssistant model in backend/app/models/league.py" (same file as T042, cannot parallel)
Task T045: "Create Tag model in backend/app/models/tag.py" (different file, CAN parallel)
Task T046: "Create League Pydantic schemas in backend/app/schemas/league.py" (different file, CAN parallel)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup → ~7 tasks
2. Complete Phase 2: Foundational → ~25 tasks (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 → ~9 tasks
4. **STOP and VALIDATE**: Test User Story 1 independently (register, login, profile management)
5. Deploy/demo if ready → **Working authentication system!**

**Total MVP**: ~41 tasks for complete authentication system

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (~32 tasks)
2. Add User Story 1 → Test independently → Deploy/Demo (~9 tasks) **MVP!**
3. Add User Story 2 → Test independently → Deploy/Demo (~13 tasks) **Leagues working!**
4. Add User Story 3 → Test independently → Deploy/Demo (~18 tasks) **Rounds working!**
5. Add User Story 4 → Test independently → Deploy/Demo (~11 tasks) **Tags working!**
6. Add User Story 5 → Test independently → Deploy/Demo (~12 tasks) **RBAC complete!**
7. Polish → Production-ready (~14 tasks) **Ship it!**

Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (~32 tasks)
2. Once Foundational is done:
   - Developer A: User Story 1 (Authentication) - fully independent
   - Developer B: User Story 2 (Leagues) after US1 authentication works
   - Developer C: User Story 5 (RBAC) - cross-cutting, can start adding permission checks
3. After US1 & US2 complete:
   - Developer A: User Story 3 (Rounds)
   - Developer B: User Story 4 (Tags)
4. Stories complete and integrate independently

---

## Task Count Summary

- **Phase 1 (Setup)**: 7 tasks
- **Phase 2 (Foundational)**: 25 tasks
- **Phase 3 (US1 - Authentication)**: 9 tasks
- **Phase 4 (US2 - Leagues/Seasons)**: 13 tasks
- **Phase 5 (US3 - Rounds/Attendance)**: 18 tasks
- **Phase 6 (US4 - Tag Rankings)**: 11 tasks
- **Phase 7 (US5 - RBAC)**: 12 tasks
- **Phase 8 (Polish)**: 14 tasks

**Total**: 109 tasks

**MVP Scope**: Phases 1-3 only (41 tasks) delivers working authentication system

---

## Notes

- [P] tasks = different files, no dependencies - can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Tests omitted per specification (no explicit TDD request) - focus on implementation
- All tasks include exact file paths from plan.md structure
- Task IDs (T001-T110) in sequential execution order
- User Story 1 is fully independent MVP after foundational phase
