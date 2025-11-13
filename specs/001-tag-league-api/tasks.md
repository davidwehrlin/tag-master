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
- **Test tasks**: Unit, contract, and integration tests for each component and user story

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
- [X] T008 [P] Write unit tests for Docker setup in backend/tests/unit/test_docker.py (verify container configuration, environment variable loading)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database Foundation

- [X] T009 Create base models in backend/app/models/base.py (BaseModel with UUID id, created_at, updated_at; SoftDeleteMixin with deleted_at)
- [X] T010 Configure async SQLAlchemy engine and session in backend/app/database.py (asyncpg driver, connection pooling 20 connections per research.md)
- [X] T011 Create Alembic migration for players table in alembic/versions/001_create_players.py (email unique index, deleted_at index per data-model.md)
- [X] T012 Create Alembic migration for leagues table in alembic/versions/002_create_leagues.py (organizer_id index, visibility index, deleted_at index)
- [X] T013 Create Alembic migration for seasons table in alembic/versions/003_create_seasons.py (league_id index, start_date/end_date composite index)
- [X] T014 Create Alembic migration for league_assistants table in alembic/versions/004_create_league_assistants.py (player_id + league_id unique constraint)
- [X] T015 Create Alembic migration for rounds table in alembic/versions/005_create_rounds.py (season_id index, date index, deleted_at index)
- [X] T016 Create Alembic migration for cards table in alembic/versions/006_create_cards.py (round_id index, creator_id index)
- [X] T017 Create Alembic migration for participations table in alembic/versions/007_create_participations.py (player_id + round_id unique constraint, status index, card_id index)
- [X] T018 Create Alembic migration for bets table in alembic/versions/008_create_bets.py (player_id index, round_id index, bet_type index)
- [X] T019 Create Alembic migration for tags table in alembic/versions/009_create_tags.py (player_id + season_id unique, season_id + tag_number unique, composite index)
- [X] T020 Create Alembic migration for tag_history table in alembic/versions/010_create_tag_history.py (player_id + season_id composite index, assignment_date index)
- [X] T021 [P] Write unit tests for base models in backend/tests/unit/test_base_models.py (test UUID generation, timestamp auto-population, soft delete behavior)
- [X] T022 [P] Write unit tests for database connection in backend/tests/unit/test_database.py (test async session factory, connection pooling configuration)

### Authentication & Authorization Foundation

- [X] T023 Implement password hashing utilities in backend/app/services/auth.py (bcrypt via passlib per research.md)
- [X] T024 Implement JWT token creation and verification in backend/app/services/auth.py (HS256 algorithm, 24hr expiration per research.md)
- [X] T025 Create OAuth2 password bearer dependency in backend/app/dependencies.py (get_current_user extracts JWT token)
- [X] T026 Create RBAC permission checking utilities in backend/app/services/permissions.py (can_manage_league, can_manage_round, is_tag_master_or_assistant)
- [X] T027 [P] Write unit tests for auth service in backend/tests/unit/test_auth_service.py (test password hashing, JWT token creation/verification, token expiration)
- [X] T028 [P] Write unit tests for permissions in backend/tests/unit/test_permissions.py (test all RBAC permission checks with various role combinations) - NOTE: Only is_tag_master tested now (6 tests); full league/round permission tests deferred to Phase 3 when models exist

### Core Infrastructure

- [X] T029 Create Pydantic settings configuration in backend/app/config.py (BaseSettings with DATABASE_URL, JWT_SECRET_KEY, CORS_ORIGINS, RATE_LIMIT_PER_MINUTE, etc.)
- [X] T030 Implement rate limiting middleware in backend/app/middleware/rate_limit.py (in-memory token bucket 50 req/min per user per research.md)
- [X] T031 [P] Implement structured logging with PII sanitization in backend/app/middleware/logging.py (structlog with custom processor to redact email, password, name, ip_address per research.md)
- [X] T032 [P] Configure CORS middleware in backend/app/middleware/cors.py (CORSMiddleware with origins from settings)
- [X] T033 [P] Implement global error handler in backend/app/middleware/error_handler.py (catch all exceptions, return ErrorResponse schema, log without PII)
- [X] T034 Create custom exception classes in backend/app/exceptions.py (AuthenticationError, AuthorizationError, NotFoundError, ValidationError, RateLimitError)
- [X] T035 Create pagination utilities in backend/app/utils/pagination.py (paginate function with total, page, size, pages metadata)
- [X] T036 Create FastAPI application in backend/app/main.py (include all middleware, routers, startup/shutdown events for database)
- [X] T037 Create health check endpoint in backend/app/api/v1/health.py (GET /health returns 200 with database status, GET /metrics returns Prometheus format per research.md)
- [X] T038 [P] Write unit tests for config in backend/tests/unit/test_config.py (test settings loading from environment, default values, validation)
- [X] T039 [P] Write unit tests for rate limiting in backend/tests/unit/test_rate_limit.py (test token bucket algorithm, per-user limits, reset behavior)
- [X] T040 [P] Write unit tests for logging middleware in backend/tests/unit/test_logging.py (test PII sanitization for email, password, name, ip_address fields)
- [X] T041 [P] Write unit tests for error handler in backend/tests/unit/test_error_handler.py (test all custom exceptions map to correct HTTP status codes and response format)
- [X] T042 [P] Write unit tests for pagination in backend/tests/unit/test_pagination.py (test pagination calculation, edge cases like page 0, negative size, total calculations)
- [ ] T043 [P] Write unit tests for dependencies in backend/tests/unit/test_dependencies.py (test get_current_user with valid/invalid tokens, soft-deleted users, missing user_id)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Player Registration & Authentication (Priority: P1) 🎯 MVP

**Goal**: Players can create accounts, log in, and manage their profiles

**Independent Test**: Create new player account, login to receive JWT token, update profile, verify changes persist

### Models for User Story 1

- [X] T044 [P] [US1] Create Player model in backend/app/models/player.py (PlayerRole enum, Player class with email, password_hash, name, bio, roles[], email_verified, soft delete per data-model.md)
- [X] T045 [P] [US1] Create Player Pydantic schemas in backend/app/schemas/player.py (PlayerRegister, PlayerLogin, TokenResponse, PlayerResponse, PlayerUpdate per contracts/openapi.yaml)

### Implementation for User Story 1

- [X] T046 [US1] Create player service in backend/app/services/player.py (register, authenticate, update, list operations following service layer pattern)
- [X] T047 [US1] Implement authentication endpoints in backend/app/api/v1/auth.py (POST /auth/register, POST /auth/login per contracts/openapi.yaml, using PlayerService)
- [X] T048 [US1] Implement player profile endpoints in backend/app/api/v1/players.py (GET /players/me, PUT /players/me, DELETE /players/me with soft delete, GET /players with pagination, GET /players/{id}, using PlayerService)
- [X] T049 [US1] Add email validation (valid format, unique across non-deleted players) in backend/app/schemas/player.py
- [X] T050 [US1] Add password validation (min 8 chars, uppercase, lowercase, number) in backend/app/schemas/player.py
- [X] T051 [US1] Add request ID correlation to logging for auth operations in backend/app/middleware/logging.py

### Testing for User Story 1

- [X] T052 [P] [US1] Write unit tests for Player model in backend/tests/unit/test_player_model.py (test PlayerRole enum, email uniqueness, soft delete behavior, role management)
- [ ] T053 [P] [US1] Write unit tests for PlayerService in backend/tests/unit/test_player_service.py (test register_player with duplicate email, authenticate_player with invalid password, update_player, soft_delete_player, list_players)
- [ ] T054 [P] [US1] Write unit tests for password validation in backend/tests/unit/test_player_service.py (test password hashing, weak passwords rejected, password complexity requirements)
- [ ] T055 [P] [US1] Write unit tests for player schemas in backend/tests/unit/test_player_schemas.py (test email validation, password validation, schema serialization)
- [ ] T056 [P] [US1] Create test fixtures in backend/tests/conftest.py (async database session, test client, authenticated user factory)
- [ ] T057 [P] [US1] Write contract tests for auth endpoints in backend/tests/contract/test_auth.py (test registration, login, invalid credentials, duplicate email)
- [ ] T058 [P] [US1] Write contract tests for player endpoints in backend/tests/contract/test_players.py (test profile retrieval, update, soft delete, list with pagination)
- [ ] T059 [US1] Write integration tests for player permissions in backend/tests/integration/test_player_permissions.py (test player can only update own profile, cannot access other profiles)

**Checkpoint**: At this point, User Story 1 should be fully functional and tested - players can register, login, view/update profiles

---

## Phase 4: User Story 2 - League Creation & Season Management (Priority: P2)

**Goal**: League organizers can create leagues, define seasons, and manage registration. Creating league auto-assigns TagMaster role.

**Independent Test**: Player creates first league (becomes TagMaster), adds season with dates, another player registers for season and receives tag

### Models for User Story 2

- [ ] T060 [P] [US2] Create League model in backend/app/models/league.py (LeagueVisibility enum, League class with name, description, rules, visibility, organizer_id, soft delete per data-model.md)
- [ ] T061 [P] [US2] Create Season model in backend/app/models/league.py (Season class with name, league_id, start_date, end_date, registration dates per data-model.md)
- [ ] T062 [P] [US2] Create LeagueAssistant model in backend/app/models/league.py (LeagueAssistant class with player_id + league_id unique constraint per data-model.md)
- [ ] T063 [P] [US2] Create Tag model in backend/app/models/tag.py (Tag class with player_id + season_id unique, season_id + tag_number unique per data-model.md)
- [ ] T064 [P] [US2] Create League Pydantic schemas in backend/app/schemas/league.py (LeagueCreate, LeagueResponse, LeagueUpdate, SeasonCreate, SeasonResponse per contracts/openapi.yaml)

### Implementation for User Story 2

- [ ] T065 [US2] Create league service in backend/app/services/league.py (create, update, delete, list operations with permission checks)
- [ ] T066 [US2] Create season service in backend/app/services/season.py (create, get, list, register_player operations)
- [ ] T067 [US2] Implement league endpoints in backend/app/api/v1/leagues.py (GET /leagues with pagination/visibility filter, POST /leagues auto-assigns TagMaster role, GET /leagues/{id}, PUT /leagues/{id}, DELETE /leagues/{id} soft delete per contracts/openapi.yaml, using LeagueService)
- [ ] T068 [US2] Implement season endpoints in backend/app/api/v1/seasons.py (GET /seasons with pagination/filters, POST /seasons, GET /seasons/{id} per contracts/openapi.yaml, using SeasonService)
- [ ] T069 [US2] Implement season registration endpoint in backend/app/api/v1/seasons.py (POST /seasons/{id}/register assigns next available tag number first-come-first-served per contracts/openapi.yaml, using SeasonService)
- [ ] T070 [US2] Add TagMaster role assignment logic in backend/app/services/league.py (call player_service.assign_tagmaster_role when creating first league)
- [ ] T071 [US2] Add league permission checks in backend/app/services/permissions.py (can_manage_league: organizer_id == current_player_id OR LeagueAssistant exists for updates/deletes per research.md)
- [ ] T072 [US2] Add season date validation (end_date after start_date, registration dates logic) in backend/app/schemas/league.py
- [ ] T073 [US2] Implement tag assignment service in backend/app/services/tag_assignment.py (assign_initial_tag function: finds max tag_number in season, increments by 1, creates Tag record)
- [ ] T074 [US2] Add soft delete validation in backend/app/services/league.py (cannot delete league with active seasons with rounds)

### Testing for User Story 2

- [ ] T075 [P] [US2] Write unit tests for League model in backend/tests/unit/test_league_models.py (test LeagueVisibility enum, relationships, soft delete, organizer relationship)
- [ ] T076 [P] [US2] Write unit tests for Season model in backend/tests/unit/test_season_models.py (test league relationship, date validation, registration date logic)
- [ ] T077 [P] [US2] Write unit tests for LeagueAssistant model in backend/tests/unit/test_league_models.py (test unique constraint on player_id + league_id)
- [ ] T078 [P] [US2] Write unit tests for Tag model in backend/tests/unit/test_tag_models.py (test unique constraints, tag_number uniqueness per season)
- [ ] T079 [P] [US2] Write unit tests for league schemas in backend/tests/unit/test_league_schemas.py (test LeagueCreate, SeasonCreate validation, date range validation)
- [ ] T080 [P] [US2] Write unit tests for LeagueService in backend/tests/unit/test_league_service.py (test create with TagMaster assignment, update permissions, soft delete validation, cannot delete with active seasons)
- [ ] T081 [P] [US2] Write unit tests for SeasonService in backend/tests/unit/test_season_service.py (test season creation, register_player with tag assignment, date validation)
- [ ] T082 [P] [US2] Write unit tests for tag assignment service in backend/tests/unit/test_tag_assignment_service.py (test assign_initial_tag finds max and increments, sequential assignment, concurrency handling)
- [ ] T083 [P] [US2] Write contract tests for league endpoints in backend/tests/contract/test_leagues.py (test league creation with TagMaster assignment, visibility filtering, update/delete permissions)
- [ ] T084 [P] [US2] Write contract tests for season endpoints in backend/tests/contract/test_seasons.py (test season creation, registration with tag assignment, date validation)
- [ ] T085 [US2] Write integration tests for league/season flow in backend/tests/integration/test_league_flow.py (test full workflow: create league → becomes TagMaster → add season → register players → tags assigned)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently and be tested - players can register/login AND create leagues/seasons with tag assignment

---

## Phase 5: User Story 3 - Round Recording & Attendance (Priority: P3)

**Goal**: Players and organizers record rounds, track attendance via participations, enter scores with peer confirmation

**Independent Test**: Create round, players register online, TagMaster checks in physically, players create cards, enter scores, confirm scores, verify all data persists

### Models for User Story 3

- [ ] T089 [P] [US3] Create Round model in backend/app/models/round.py (Round class with season_id, creator_id, date, course_name, location, start_time, soft delete per data-model.md)
- [ ] T090 [P] [US3] Create Card model in backend/app/models/round.py (Card class with round_id, creator_id per data-model.md)
- [ ] T091 [P] [US3] Create Participation model in backend/app/models/round.py (ParticipationStatus enum, Participation class with player_id + round_id unique, card_id, status, timestamps, score fields per data-model.md)
- [ ] T092 [P] [US3] Create Bet model in backend/app/models/bet.py (BetType enum, Bet class with player_id, round_id, bet_type, amount, description per data-model.md)
- [ ] T093 [P] [US3] Create Round Pydantic schemas in backend/app/schemas/round.py (RoundCreate, RoundResponse, ParticipationCreate, PhysicalParticipation, ParticipationResponse, CardCreate, CardResponse, ScoreEntry, ScoreConfirmation per contracts/openapi.yaml)
- [ ] T094 [P] [US3] Create Bet Pydantic schemas in backend/app/schemas/bet.py (BetCreate, BetResponse per contracts/openapi.yaml)

### Implementation for User Story 3

- [ ] T095 [US3] Create round service in backend/app/services/round.py (create, get, delete, list operations with permission checks)
- [ ] T096 [US3] Create participation service in backend/app/services/participation.py (register, physical_checkin, mark_dnf operations with validation)
- [ ] T097 [US3] Create card service in backend/app/services/card.py (create, get operations with player validation)
- [ ] T098 [US3] Create score service in backend/app/services/score.py (enter_score, confirm_score operations with validation)
- [ ] T099 [US3] Create bet service in backend/app/services/bet.py (record_bet, list_bets operations)
- [ ] T100 [US3] Implement round endpoints in backend/app/api/v1/rounds.py (GET /rounds with pagination/filters, POST /rounds TagMaster/Assistant only, GET /rounds/{id}, DELETE /rounds/{id} soft delete per contracts/openapi.yaml, using RoundService)
- [ ] T101 [US3] Implement participation endpoints in backend/app/api/v1/participations.py (GET /rounds/{id}/participations with status filter, POST /rounds/{id}/participations for online registration, POST /rounds/{id}/participations/physical TagMaster/Assistant only, POST /participations/{id}/dnf per contracts/openapi.yaml, using ParticipationService)
- [ ] T102 [US3] Implement card endpoints in backend/app/api/v1/cards.py (POST /cards with 3-6 checked-in players, GET /cards/{id} per contracts/openapi.yaml, using CardService)
- [ ] T103 [US3] Implement score endpoints in backend/app/api/v1/scores.py (POST /cards/{id}/scores card creator only, POST /cards/{id}/scores/confirm non-creator only per contracts/openapi.yaml, using ScoreService)
- [ ] T104 [US3] Implement bet endpoints in backend/app/api/v1/bets.py (GET /rounds/{id}/bets with bet_type filter per contracts/openapi.yaml, using BetService)
- [ ] T105 [US3] Add round permission checks in backend/app/services/permissions.py (creator must be TagMaster or Assistant for league)
- [ ] T106 [US3] Add participation validation in backend/app/services/participation.py (cannot register twice for same round, physical check-in updates status and timestamp)
- [ ] T107 [US3] Add card validation in backend/app/services/card.py (3-6 players minimum/maximum, all players must have status=checked_in, each player only on one card per round)
- [ ] T108 [US3] Add score validation in backend/app/services/score.py (can only enter score if status=checked_in, score_entered_by_id must be card creator)
- [ ] T109 [US3] Add score confirmation validation in backend/app/services/score.py (cannot confirm own score, must be different card member, updates status to completed)
- [ ] T110 [US3] Add DNF logic in backend/app/services/participation.py (marks participation status=dnf, final state, excluded from tag reassignment)
- [ ] T111 [US3] Add bet validation in backend/app/services/bet.py (amount must be positive, player must be checked in, recorded during physical participation)

### Testing for User Story 3

- [ ] T112 [P] [US3] Write unit tests for Round model in backend/tests/unit/test_round_models.py (test season relationship, creator relationship, soft delete, date validation)
- [ ] T113 [P] [US3] Write unit tests for Card model in backend/tests/unit/test_card_models.py (test round relationship, creator relationship, participation relationships)
- [ ] T114 [P] [US3] Write unit tests for Participation model in backend/tests/unit/test_participation_models.py (test ParticipationStatus enum, unique constraint on player_id + round_id, status transitions)
- [ ] T115 [P] [US3] Write unit tests for Bet model in backend/tests/unit/test_bet_models.py (test BetType enum, relationships, amount validation)
- [ ] T116 [P] [US3] Write unit tests for round schemas in backend/tests/unit/test_round_schemas.py (test RoundCreate, ParticipationCreate, CardCreate, ScoreEntry validation)
- [ ] T117 [P] [US3] Write unit tests for RoundService in backend/tests/unit/test_round_service.py (test create with permission checks, soft delete, list with filters)
- [ ] T118 [P] [US3] Write unit tests for ParticipationService in backend/tests/unit/test_participation_service.py (test register, physical_checkin updates status and timestamp, mark_dnf, duplicate prevention)
- [ ] T119 [P] [US3] Write unit tests for CardService in backend/tests/unit/test_card_service.py (test create with 3-6 player validation, checked-in status requirement, one card per player per round)
- [ ] T120 [P] [US3] Write unit tests for ScoreService in backend/tests/unit/test_score_service.py (test enter_score validation, confirm_score validation, cannot confirm own score, status updates)
- [ ] T121 [P] [US3] Write unit tests for BetService in backend/tests/unit/test_bet_service.py (test record_bet validation, amount positive check, player checked-in requirement)
- [ ] T122 [P] [US3] Write contract tests for round endpoints in backend/tests/contract/test_rounds.py (test round creation by TagMaster/Assistant, list with filters, soft delete)
- [ ] T123 [P] [US3] Write contract tests for participation endpoints in backend/tests/contract/test_participations.py (test online registration, physical check-in, DNF marking, duplicate prevention)
- [ ] T124 [P] [US3] Write contract tests for card endpoints in backend/tests/contract/test_cards.py (test card creation with 3-6 players, validation)
- [ ] T125 [P] [US3] Write contract tests for score endpoints in backend/tests/contract/test_scores.py (test score entry by creator, confirmation by non-creator, cannot confirm own)
- [ ] T126 [P] [US3] Write contract tests for bet endpoints in backend/tests/contract/test_bets.py (test bet recording during physical check-in, bet_type filtering)
- [ ] T127 [US3] Write integration tests for round flow in backend/tests/integration/test_round_flow.py (test full workflow: register → check-in → create card → enter scores → confirm → status completed)

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently and be tested - complete round workflow with attendance, cards, scores, and confirmation

---

## Phase 6: User Story 4 - Tag-Based Rankings & Statistics (Priority: P4)

**Goal**: View current tag holders, tag history, and dynamic tag reassignment after each round based on performance

**Independent Test**: View season tag standings, complete round with confirmed scores, verify tags reassigned (best score gets Tag #1), view tag history showing progression

### Models for User Story 4

- [ ] T128 [P] [US4] Create TagHistory model in backend/app/models/tag.py (TagHistory class with tag_number, player_id, season_id, round_id, assignment_date, append-only per data-model.md)
- [ ] T129 [P] [US4] Create Tag Pydantic schemas in backend/app/schemas/tag.py (TagResponse with is_eligible field, TagHistoryResponse per contracts/openapi.yaml)

### Implementation for User Story 4

- [ ] T130 [US4] Implement tag standings endpoint in backend/app/api/v1/tags.py (GET /seasons/{id}/tags sorted by tag_number with eligible_only filter per contracts/openapi.yaml, using tag_assignment service)
- [ ] T131 [US4] Implement tag history endpoint in backend/app/api/v1/tags.py (GET /players/{id}/tags/history with season filter per contracts/openapi.yaml, using tag_assignment service)
- [ ] T132 [US4] Implement eligibility calculation service in backend/app/services/eligibility.py (check_eligibility function: minimum 3 completed rounds in league season-independent, 1 round in last 5 rounds of season, exclude DNF per research.md)
- [ ] T133 [US4] Implement tag reassignment algorithm in backend/app/services/tag_assignment.py (reassign_tags_after_round function: O(n log n) sorting by score then previous tag_number, single transaction with SELECT FOR UPDATE per research.md)
- [ ] T134 [US4] Add tag reassignment trigger in backend/app/services/score.py (call tag_assignment.reassign_tags_after_round when all scores confirmed for round, only reassign participating players excluding DNF)
- [ ] T135 [US4] Add TagHistory record creation in backend/app/services/tag_assignment.py (create history entry on initial tag assignment and after each reassignment with round_id)
- [ ] T136 [US4] Add tie-breaking logic in backend/app/services/tag_assignment.py (player with lower tag_number before round keeps better tag on tie)
- [ ] T137 [US4] Add eligibility indicator in backend/app/api/v1/tags.py (call eligibility.check_eligibility for each player, add is_eligible boolean to TagResponse)
- [ ] T138 [US4] Add validation for end-of-season eligibility display in backend/app/services/eligibility.py (apply eligibility rules only to standings display, not round-by-round reassignment per spec.md clarification)

### Testing for User Story 4

- [ ] T139 [P] [US4] Write unit tests for TagHistory model in backend/tests/unit/test_tag_history_models.py (test append-only behavior, relationships, composite indexes)
- [ ] T140 [P] [US4] Write unit tests for tag schemas in backend/tests/unit/test_tag_schemas.py (test TagResponse with is_eligible field, TagHistoryResponse serialization)
- [ ] T141 [P] [US4] Write unit tests for eligibility service in backend/tests/unit/test_eligibility_service.py (test 3-round minimum, last 5 rounds requirement, DNF exclusion, season-independent calculation)
- [ ] T142 [P] [US4] Write unit tests for tag reassignment algorithm in backend/tests/unit/test_tag_assignment_service.py (test sorting by score, tie-breaking by previous tag_number, transaction handling with SELECT FOR UPDATE)
- [ ] T143 [P] [US4] Write unit tests for TagHistory creation in backend/tests/unit/test_tag_assignment_service.py (test history entry on initial assignment, history entry on reassignment with round_id)
- [ ] T144 [P] [US4] Write contract tests for tag endpoints in backend/tests/contract/test_tags.py (test tag standings with eligibility filter, tag history retrieval with season filter)
- [ ] T145 [US4] Write integration tests for tag reassignment in backend/tests/integration/test_tag_reassignment.py (test full workflow: complete round → all scores confirmed → tags reassigned → history recorded → eligibility calculated)

**Checkpoint**: At this point, User Stories 1-4 should all work independently - complete tag lifecycle with reassignment and eligibility tracking

---

## Phase 7: User Story 5 - Role-Based Access Control (Priority: P5)

**Goal**: Enforce role-based permissions ensuring players can only modify own data while TagMasters/Assistants can manage leagues

**Independent Test**: Attempt various operations as different role types (Player, TagMaster, Assistant) and verify proper authorization

### Models for User Story 5

- [ ] T146 [P] [US5] Create Assistant Pydantic schemas in backend/app/schemas/assistant.py (AssistantAssign, AssistantResponse per contracts/openapi.yaml)

### Implementation for User Story 5

- [ ] T147 [US5] Create assistant service in backend/app/services/assistant.py (assign, revoke, list operations with permission checks)
- [ ] T148 [US5] Implement assistant management endpoints in backend/app/api/v1/assistants.py (GET /leagues/{id}/assistants, POST /leagues/{id}/assistants TagMaster only, DELETE /leagues/{id}/assistants/{player_id} TagMaster only per contracts/openapi.yaml, using AssistantService)
- [ ] T149 [US5] Add assistant assignment logic in backend/app/services/assistant.py (create LeagueAssistant record, assigner must be TagMaster or league organizer)
- [ ] T150 [US5] Add assistant revocation logic in backend/app/services/assistant.py (delete LeagueAssistant record, only TagMaster can revoke)
- [ ] T151 [US5] Add league-specific assistant permission checks in backend/app/services/permissions.py (can_manage_league checks organizer_id OR LeagueAssistant exists for player+league)
- [ ] T152 [US5] Enhance player profile permission checks in backend/app/services/player.py (validate can only update/delete own profile)
- [ ] T153 [US5] Enhance round creation permission checks in backend/app/services/permissions.py (creator must be TagMaster or Assistant for the league)
- [ ] T154 [US5] Enhance physical participation permission checks in backend/app/services/permissions.py (only TagMaster or Assistant can perform physical check-in)
- [ ] T155 [US5] Enhance score entry permission checks in backend/app/services/permissions.py (only card creator can enter scores)
- [ ] T156 [US5] Enhance score confirmation permission checks in backend/app/services/permissions.py (only non-creator card members can confirm)
- [ ] T157 [US5] Enhance DNF marking permission checks in backend/app/services/permissions.py (card creator or TagMaster/Assistant can mark DNF)
- [ ] T158 [US5] Add public league read access in backend/app/services/league.py (any authenticated user can view public leagues)
- [ ] T159 [US5] Add cascade delete for LeagueAssistant when league deleted in backend/app/models/league.py (relationship cascade configuration)

### Testing for User Story 5

- [ ] T160 [P] [US5] Write unit tests for assistant schemas in backend/tests/unit/test_assistant_schemas.py (test AssistantAssign, AssistantResponse validation)
- [ ] T161 [P] [US5] Write unit tests for AssistantService in backend/tests/unit/test_assistant_service.py (test assign, revoke, list operations with permission validation, cannot assign non-existent player)
- [ ] T162 [P] [US5] Write unit tests for enhanced permissions in backend/tests/unit/test_permissions.py (test all RBAC scenarios: Player, TagMaster, Assistant access patterns across all operations)
- [ ] T163 [P] [US5] Write contract tests for assistant endpoints in backend/tests/contract/test_assistants.py (test assignment by TagMaster, revocation, list, unauthorized attempts)
- [ ] T164 [US5] Write integration tests for RBAC in backend/tests/integration/test_rbac.py (test full permission scenarios across all user stories: profile updates, league management, round creation, score entry)

**Checkpoint**: All user stories should now be independently functional with proper role-based access control across all operations

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T165 [P] Add Prometheus metrics collection in backend/app/api/v1/health.py (http_requests_total, http_request_duration_seconds, error rates per research.md)
- [ ] T166 [P] Add webhook alerts for monitoring thresholds in backend/app/middleware/logging.py (error rate > 5%, p95 latency > 500ms per research.md)
- [ ] T167 [P] Add comprehensive input validation across all services (sanitize strings, validate UUIDs, check date ranges)
- [ ] T168 [P] Add pagination to all list operations in services (leagues, seasons, rounds, tags, participations per contracts/openapi.yaml)
- [ ] T169 [P] Optimize database queries with eager loading in backend/app/services/ (use selectin loading for relationships to avoid N+1 queries per research.md)
- [ ] T170 [P] Add database query plan analysis for complex queries in backend/app/services/ (eligibility calculation, tag standings)
- [ ] T171 [P] Add comprehensive error messages without exposing sensitive data in backend/app/exceptions.py
- [ ] T172 [P] Update quickstart.md with complete API usage examples (11 curl commands covering full workflow)
- [ ] T173 [P] Generate OpenAPI documentation in backend/app/main.py (FastAPI auto-generates at /docs and /redoc)
- [ ] T174 [P] Add health check validation (database connectivity check with timeout) in backend/app/api/v1/health.py
- [ ] T175 [P] Add graceful shutdown handling in backend/app/main.py (handle SIGTERM/SIGINT, 2 sec delay for in-flight requests per research.md)
- [ ] T176 Run quickstart.md validation (docker-compose up, run migrations, test all 11 API examples, verify health endpoint)
- [ ] T177 Add rate limit headers to all responses in backend/app/middleware/rate_limit.py (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)
- [ ] T178 Add soft delete filtering to all queries in backend/app/services/ (exclude deleted_at != null for players and rounds)

### Testing for Phase 8

- [ ] T179 [P] Write unit tests for metrics collection in backend/tests/unit/test_metrics.py (test Prometheus metrics recording, http_requests_total counter, duration histogram)
- [ ] T180 [P] Write unit tests for query optimization in backend/tests/unit/test_query_optimization.py (test eager loading prevents N+1 queries, verify selectin loading)
- [ ] T181 [P] Write unit tests for soft delete filtering in backend/tests/unit/test_soft_delete.py (test deleted records excluded from all queries)
- [ ] T182 [P] Write integration tests for complete API workflow in backend/tests/integration/test_full_workflow.py (test all 11 quickstart.md scenarios end-to-end)

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

- **Phase 1 (Setup)**: All tasks marked [P] can run in parallel (T006, T007, T008, T009, T010)
- **Phase 2 (Foundational)**: All tasks marked [P] can run in parallel within categories:
  - Migrations: T013-T022 can run sequentially (order matters for foreign keys)
  - Infrastructure: T029, T030, T031 can run in parallel (different middleware files)
- **User Story phases**: All models marked [P] within a story can run in parallel
- **Different user stories**: Can be worked on in parallel by different team members after Phase 2 completes

---

## Parallel Example: User Story 1

```bash
# Launch both models for User Story 1 together:
Task T036: "Create Player model in backend/app/models/player.py"
Task T037: "Create Player Pydantic schemas in backend/app/schemas/player.py"

# These run in parallel because they're in different files with no dependencies
```

## Parallel Example: User Story 2

```bash
# Launch all models for User Story 2 together:
Task T045: "Create League model in backend/app/models/league.py"
Task T046: "Create Season model in backend/app/models/league.py" (same file as T045, cannot parallel)
Task T047: "Create LeagueAssistant model in backend/app/models/league.py" (same file as T045, cannot parallel)
Task T048: "Create Tag model in backend/app/models/tag.py" (different file, CAN parallel)
Task T049: "Create League Pydantic schemas in backend/app/schemas/league.py" (different file, CAN parallel)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup → 8 tasks
2. Complete Phase 2: Foundational → 34 tasks (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 → 16 tasks
4. **STOP and VALIDATE**: Test User Story 1 independently (register, login, profile management)
5. Deploy/demo if ready → **Working authentication system!**

**Total MVP**: 58 tasks for complete authentication system with comprehensive tests

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready (42 tasks)
2. Add User Story 1 → Test independently → Deploy/Demo (16 tasks) **MVP!**
3. Add User Story 2 → Test independently → Deploy/Demo (26 tasks) **Leagues working!**
4. Add User Story 3 → Test independently → Deploy/Demo (39 tasks) **Rounds working!**
5. Add User Story 4 → Test independently → Deploy/Demo (18 tasks) **Tags working!**
6. Add User Story 5 → Test independently → Deploy/Demo (19 tasks) **RBAC complete!**
7. Polish → Production-ready (18 tasks) **Ship it!**

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

- **Phase 1 (Setup)**: 8 tasks (7 implementation + 1 test task)
- **Phase 2 (Foundational)**: 34 tasks (21 implementation + 13 test tasks)
  - Database: 12 tasks (10 migrations + 2 tests)
  - Auth: 6 tasks (4 implementation + 2 tests)
  - Infrastructure: 16 tasks (9 implementation + 7 tests)
- **Phase 3 (US1 - Authentication)**: 16 tasks (8 implementation + 8 test tasks)
- **Phase 4 (US2 - Leagues/Seasons)**: 26 tasks (15 implementation + 11 test tasks)
- **Phase 5 (US3 - Rounds/Attendance)**: 39 tasks (23 implementation + 16 test tasks)
- **Phase 6 (US4 - Tag Rankings)**: 18 tasks (11 implementation + 7 test tasks)
- **Phase 7 (US5 - RBAC)**: 19 tasks (14 implementation + 5 test tasks)
- **Phase 8 (Polish)**: 18 tasks (14 implementation + 4 test tasks)

**Total**: 178 tasks (106 implementation + 72 test tasks)

**Total**: 101 tasks (reduced from 109 due to service layer consolidation)

**MVP Scope**: Phases 1-3 only (~38 tasks) delivers working authentication system with service layer architecture

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
- Task IDs (T004-T179) in sequential execution order
- User Story 1 is fully independent MVP after foundational phase
- **Service Layer Pattern**: Business logic resides in `services/`, API endpoints are thin HTTP wrappers
