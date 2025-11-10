# Feature Specification: Disc Golf Tag League API

**Feature Branch**: `001-tag-league-api`  
**Created**: 2025-11-08  
**Status**: Draft  
**Input**: User description: "Build a FastAPI Python application that acts as a backend for a disc golf tag league tracking system with Users, Players, Roles, Leagues, Seasons, TagMasters, Rounds, and Participations, each with CRUD REST API endpoints"

**Project Structure**: All backend API code will be located in `backend/` folder at repository root to maintain separation from future frontend implementation.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Player Registration & Authentication (Priority: P1)

Players can create accounts, log in, and manage their profiles. This is the foundation for all other functionality as every player needs an authenticated account to participate.

**Why this priority**: Without authentication, no other features can function. This is the entry point for all users and must be rock-solid.

**Independent Test**: Can be fully tested by creating a new player account, logging in, updating profile information, and logging out. Delivers value by allowing players to establish their identity in the system.

**Acceptance Scenarios**:

1. **Given** a new player visits the system, **When** they provide email, password, and basic info, **Then** their account is created and they receive a confirmation
2. **Given** an existing player with valid credentials, **When** they log in, **Then** they receive an authentication token and can access protected endpoints
3. **Given** an authenticated player, **When** they update their profile information, **Then** changes are saved and reflected immediately
4. **Given** an authenticated player, **When** they request password reset, **Then** they can securely reset their password via email

---

### User Story 2 - League Creation & Season Management (Priority: P2)

League organizers (players who create leagues) can create leagues, define seasons within those leagues, and manage season registration. Players can browse available leagues and register for specific seasons. Creating a league automatically grants TagMaster role.

**Why this priority**: Once players can authenticate, they need leagues and seasons to join. This enables the core organizational structure of the tag league system.

**Independent Test**: Can be tested by a player creating their first league (auto-assigned TagMaster role), adding a season with registration dates, and another player registering for that season. Delivers value by establishing the competitive structure.

**Acceptance Scenarios**:

1. **Given** a player without TagMaster role, **When** they create a new league with name, description, and visibility setting, **Then** the league is created with public or private status and they are automatically assigned TagMaster role
2. **Given** a league organizer, **When** they create a season with start/end dates, **Then** the season is created and open for registration throughout its duration
3. **Given** an authenticated player and public season, **When** they register for that season at any time, **Then** their registration is recorded and they can participate
4. **Given** a player and private league, **When** they request access, **Then** the request is pending until organizer approval
5. **Given** a league organizer, **When** they view access requests for their private league, **Then** they can approve or deny requests
6. **Given** a league organizer, **When** they invite a player to their private league, **Then** the player receives an invitation they can accept

---

### User Story 3 - Round Recording & Attendance (Priority: P3)

Players and organizers can record disc golf rounds, track attendance via check-ins, and record scores. This captures the actual gameplay data.

**Why this priority**: With leagues and seasons established, players need to record their actual games. This is the core activity tracking feature.

**Independent Test**: Can be tested by creating a round at a specific course/location, checking in participating players, and recording their scores. Delivers value by tracking actual gameplay.

**Acceptance Scenarios**:

1. **Given** a TagMaster in an active season, **When** they create a round with date, course, location, and start time, **Then** the round is created and ready for online registration
2. **Given** an upcoming round, **When** players pre-register online, **Then** their online registration is recorded but they are not yet checked in
3. **Given** a round at its scheduled start time, **When** the TagMaster physically checks in players by entering their names, **Then** each player's physical attendance is recorded with timestamp
4. **Given** a player checking in physically, **When** the TagMaster asks about bet participation, **Then** the TagMaster can record ACE pot, CTP, or challenge bets with amounts and collects physical money
5. **Given** physical check-in is complete, **When** a player creates a card with 3-6 checked-in players, **Then** the card is associated with that round
6. **Given** a card has finished playing the round, **When** the card creator records scores for all physically checked-in players in their card, **Then** scores are saved with stroke counts
7. **Given** a player abandons the card mid-round for an emergency, **When** the card creator or league organizer removes them from the card, **Then** the player is marked as DNF (Did Not Finish) and excluded from tag reassignment
8. **Given** a player who only registered online without physical check-in, **When** someone attempts to record their score, **Then** the system prevents score entry
9. **Given** a completed round with all scores entered, **When** the round is finalized, **Then** all participating players' tags are reassigned based on their round performance (excluding DNF players)
10. **Given** a completed round with multiple cards, **When** anyone views it, **Then** they see all cards, participants, stroke count scores, DNF status, bet participation, and resulting tag changes
11. **Given** a card creator, **When** they attempt to edit scores, **Then** they can only modify scores for players in their card who physically checked in

---

### User Story 4 - Tag-Based Rankings & Statistics (Priority: P4)

Players and organizers can view current tag holders, tag assignment history, and player statistics. The tag system provides dynamic competitive rankings where positions are won/lost after each round.

**Why this priority**: After capturing round data, players need to see their current tag position and track competitive progression. This creates engagement through dynamic, round-by-round competition.

**Independent Test**: Can be tested by viewing a season's tag standings showing current tag holders (Tag #1, #2, #3, etc.), completing a round, and verifying tags are reassigned based on performance. Delivers value by showing competitive hierarchy.

**Acceptance Scenarios**:

1. **Given** a new season, **When** players register, **Then** they receive tags on first-come-first-served basis (first player gets Tag #1, second gets Tag #2, etc.)
2. **Given** a completed round with confirmed scores, **When** the round is finalized, **Then** all participating players' tags are reassigned based on round performance (best score gets Tag #1, etc.)
3. **Given** a card with entered scores, **When** at least one non-creator card member confirms the scores, **Then** the scores become official and can be used for tag reassignment
4. **Given** a player joining mid-season, **When** they register, **Then** they receive the next highest incremented tag number
5. **Given** a season with multiple rounds, **When** anyone views tag standings, **Then** they see current tag holders sorted by tag number with eligibility status
6. **Given** an authenticated player, **When** they view their own statistics, **Then** they see current tag, tag history, total rounds, average score, best score, and career statistics
7. **Given** a league organizer, **When** they view season analytics, **Then** they see participation rates, tag progression charts, and eligibility warnings (minimum 3 rounds, 1 in last 5)
8. **Given** official season standings, **When** eligibility is calculated, **Then** only players with minimum 3 rounds in league AND 1 round in last 5 rounds of season are marked eligible

---

### User Story 5 - Role-Based Access Control (Priority: P5)

The system enforces role-based permissions ensuring players can only modify their own data while TagMasters and Assistants can manage leagues, approve submissions, and moderate content.

**Why this priority**: Security and data integrity become critical as the system scales. This ensures proper access controls are in place.

**Independent Test**: Can be tested by attempting various operations as different role types and verifying proper authorization. Delivers value by protecting data integrity.

**Acceptance Scenarios**:

1. **Given** a regular player, **When** they attempt to create a league, **Then** the league is created and they are automatically assigned TagMaster role
2. **Given** a TagMaster, **When** they attempt to edit any league they created, **Then** the operation succeeds
3. **Given** a TagMaster, **When** they grant Assistant role to another player for their league, **Then** that player can perform league management operations for that league only
4. **Given** an Assistant, **When** they attempt to manage a league they are assigned to, **Then** the operation succeeds
5. **Given** an Assistant, **When** they attempt to manage a league they are NOT assigned to, **Then** the request is denied
6. **Given** a player, **When** they attempt to modify another player's profile, **Then** the request is denied
7. **Given** any authenticated user, **When** they attempt to view public league information, **Then** they can access read-only data

---

### Edge Cases

- What happens when a player joins a season mid-season? (Receives next highest tag number; must still meet eligibility requirements)
- What happens when tags need to be reassigned but some players didn't participate in that round? (Only participating players' tags are reassigned; non-participants keep current tags)
- What happens when two players tie with the same score? (Player with lower tag number before the round keeps the better tag)
- What happens if no card member confirms scores within 2 hours? (Round becomes stuck; TagMaster must manually approve; 2-hour window starts when scores are submitted) **[FRONTEND-TODO: Timer UI]**
- What happens if a card member disputes already-confirmed scores? (TagMaster can mark as disputed and investigate)
- How does the card creator get notified that confirmation is needed? (System displays pending confirmation message for card creator) **[FRONTEND-TODO: Notification UI]**
- Can a player be on multiple cards in the same round? (No - each player can only be assigned to one card per round)
- What if only 2 participants play and they come in with 2 tags? (Nothing changes - they keep their existing tags)
- What happens if someone doesn't play for weeks? (They keep their tag but won't be in end-of-season rankings if they haven't played in last 5 rounds)
- What happens if a player abandons their card mid-round for an emergency? (Card creator or league organizer removes them from card; player marked as DNF; excluded from tag reassignment; bet money forfeited to pot)
- Can a removed/DNF player be re-added to the card? (Out of scope for MVP - once removed, status is final)
- Does a DNF count toward the "3 rounds in league" eligibility requirement? (No - DNF rounds don't count toward eligibility)
- What's the minimum card size? (3 players minimum)
- If a card has 4 players and 1 is marked DNF, how many confirmations are needed? (Still need 1 non-creator confirmation from remaining 2 non-DNF players)
- What happens to data created by an Assistant when they're removed from a league? (Ownership transfers to league's TagMaster; only TagMaster can edit that data)
- How does the system handle duplicate participations (same player registering for the same round twice)?
- What happens if a TagMaster tries to physically check in a player who isn't registered for the season?
- What happens if a player only registers online but never physically checks in? (Cannot have scores entered; not counted in round results)
- What happens when a player is deleted but has historical round data, bet records, and tag history?
- How does the system handle concurrent updates to the same card scores by different players?
- What happens when a season end date is changed after rounds have been recorded?
- How is "last 5 rounds of season" calculated if season has fewer than 5 completed rounds? (All rounds count as "last 5")
- How does the system handle players in multiple leagues with overlapping seasons? (Each season has independent tag assignments)
- What happens when a player creates their first league? (Automatically assigned TagMaster role)
- Can a player lose TagMaster role? (Out of scope for MVP - once assigned, role persists)
- What happens when a TagMaster role is revoked from a league organizer mid-season? (Out of scope - role persists for MVP)
- Can an Assistant grant Assistant privileges to other players? (No - only TagMasters can grant/revoke Assistant role)
- Can an Assistant manage multiple leagues? (Yes - they can be assigned Assistant role for multiple leagues by different TagMasters)
- Can an Assistant create new leagues? (Yes - they become TagMaster for leagues they create)
- What happens when an Assistant is removed from a league mid-season? (They lose permissions for that league; rounds/data they created remain intact)
- What happens when a TagMaster deletes a league? (All Assistant role assignments for that league are automatically removed)
- What happens when a card creator tries to edit scores for players not in their card?
- What happens when someone tries to enter a score for a player who didn't physically check in?
- How does the system handle private league access requests when the organizer is inactive?
- What happens when a player is removed from a season but has recorded rounds and tag history?
- How are eligibility requirements enforced when "minimum 3 rounds in league" is season-independent? (Count rounds across all seasons in that league)
- How are bet winnings calculated and tracked? (Out of scope for MVP - tracking only)
- What happens when a TagMaster records a bet but forgets to collect the money?
- How does the system handle refunds for cancelled rounds with recorded bets and tag reassignments?
- What monitoring metrics are most critical for API health? (Error rate, response time p95, health check status)
- How are monitoring notification thresholds configured? (Environment variables or config file)
- What happens when monitoring notification delivery fails? (Logged as error; retry logic recommended)
- How does the stateless API handle concurrent requests from multiple container instances? (Database transactions and row-level locking ensure consistency)
- What happens when a container instance crashes mid-request? (Client receives timeout/error; can retry request safely for idempotent operations)
- How are database migrations handled across multiple container instances? (Run migrations as separate deployment step before scaling up containers)
- What exactly counts as PII in logs? (Emails, names, passwords, tokens, IP addresses, any data that identifies individuals)
- What if PII accidentally gets logged? (Log sanitization should catch and redact; implement log monitoring/alerts for PII patterns)
- How are errors logged without exposing PII? (Use user_id instead of email, redact sensitive fields, log error types not full messages)

## Requirements *(mandatory)*

### Functional Requirements

**Authentication & Authorization**
- **FR-001**: System MUST provide JWT-based authentication for all players
- **FR-002**: System MUST support email/password authentication with secure password hashing (bcrypt or argon2)
- **FR-003**: System MUST enforce role-based access control (Player, TagMaster, Assistant roles)
- **FR-004**: System MUST allow players to reset forgotten passwords via email with time-limited secure tokens
- **FR-005**: System MUST validate email uniqueness during registration
- **FR-006**: System MUST expire JWT tokens after configurable time period (default 24 hours)
- **FR-007**: System MUST validate JWT tokens on all protected endpoints
- **FR-008**: System MUST return 401 Unauthorized for invalid or expired tokens
- **FR-009**: System MUST return 403 Forbidden when authenticated users lack required permissions
- **FR-010**: System MUST rate limit authentication attempts to prevent brute force attacks (max 5 attempts per minute per IP)
- **FR-011**: System MUST validate that players can only modify their own data unless they have TagMaster or Assistant role
- **FR-012**: System MUST validate that only league organizers can modify their own leagues and seasons
- **FR-116**: System MUST automatically assign TagMaster role to any player when they create their first league
- **FR-119**: System MUST allow TagMasters to grant Assistant role to other players for specific leagues
- **FR-120**: System MUST allow TagMasters to revoke Assistant role from players for specific leagues
- **FR-121**: System MUST scope Assistant permissions to specific leagues (not global like TagMaster)
- **FR-128**: System MUST allow Assistants to create new leagues (becoming TagMaster for those leagues automatically)
- **FR-129**: System MUST remove Assistant role assignment when the associated league is deleted
- **FR-137**: System MUST transfer ownership of rounds/cards/scores to the league's TagMaster when an Assistant is removed from that league

**Security & CORS**
- **FR-096**: System MUST implement CORS (Cross-Origin Resource Sharing) with configurable allowed origins
- **FR-097**: System MUST sanitize all user input to prevent SQL injection attacks
- **FR-098**: System MUST sanitize all user input to prevent XSS (Cross-Site Scripting) attacks
- **FR-099**: System MUST use parameterized queries or ORM for all database operations
- **FR-100**: System MUST validate all request payloads against defined schemas
- **FR-101**: System MUST implement rate limiting on all endpoints (50 requests per minute per authenticated user)
- **FR-102**: System MUST use HTTPS in production environments (enforce via configuration)
- **FR-103**: System MUST not expose sensitive information in error messages (stack traces, database details)
- **FR-104**: System MUST implement request size limits to prevent denial of service attacks
- **FR-105**: System MUST log all authentication failures and authorization violations for security auditing (without logging PII)
- **FR-106**: System MUST implement secure password reset flow with email verification
- **FR-107**: System MUST enforce password complexity requirements (minimum length, character types)
- **FR-130**: System MUST make email verification optional during account registration

**Player Management**
- **FR-013**: System MUST allow players to create accounts with email, password, name, and optional profile information
- **FR-014**: System MUST allow players to update their own profile information
- **FR-015**: System MUST allow players to view other player profiles (read-only)
- **FR-016**: System MUST support soft deletion of player accounts (preserve historical data)
- **FR-123**: System MUST support soft deletion of rounds (preserve historical data and tag history)

**League & Season Management**
- **FR-017**: System MUST allow TagMasters to create leagues with name, description, rules, and visibility settings (public/private)
- **FR-018**: System MUST allow league organizers (TagMasters and Assistants) to create seasons with start date, end date, and registration period
- **FR-019**: System MUST allow players to register for seasons at any time throughout the season duration
- **FR-020**: System MUST allow players to browse all public leagues and seasons
- **FR-021**: System MUST support independent seasons within leagues (no hierarchy, separate registrations)
- **FR-022**: System MUST allow league organizers (TagMasters and Assistants) to update league and season information
- **FR-023**: System MUST support private leagues that require invitation or approval to join
- **FR-024**: System MUST allow league organizers (TagMasters and Assistants) to invite players to private leagues
- **FR-025**: System MUST allow players to request access to private leagues pending organizer approval
- **FR-122**: System MUST allow league organizers (TagMasters and Assistants) to approve/deny access requests for private leagues

**Round & Participation Management**
- **FR-026**: System MUST allow league organizers (TagMasters and Assistants) to create rounds for a season with date, course name, and location
- **FR-027**: System MUST allow league organizers (TagMasters and Assistants) to perform physical check-ins by entering player names at the course
- **FR-028**: System MUST record participation timestamps for attendance tracking
- **FR-029**: System MUST allow league organizers (TagMasters and Assistants) to record optional bet participation during physical check-in (ACE pot, CTP, random challenges)
- **FR-030**: System MUST allow score recording for checked-in players using traditional disc golf scoring (stroke count)
- **FR-031**: System MUST associate rounds with specific seasons
- **FR-032**: System MUST support multiple players per round organized in cards (minimum 3 players, typically 3-6 players)
- **FR-033**: System MUST allow card creators to enter scores for all players in their card
- **FR-034**: System MUST allow players to join rounds throughout the season (open registration)
- **FR-117**: System MUST allow card creation only after physical check-in is completed
- **FR-118**: System MUST allow players to create cards from the checked-in players list
- **FR-124**: System MUST prevent a player from being assigned to multiple cards in the same round
- **FR-125**: System MUST start the 2-hour score confirmation window when scores are submitted (not when round ends)
- **FR-131**: System MUST allow card creators or league organizers to remove a player from a card (for emergencies/abandonment)
- **FR-132**: System MUST mark removed players as "Did Not Finish" (DNF) status
- **FR-133**: System MUST exclude DNF players from tag reassignment calculations at round completion
- **FR-134**: System MUST validate minimum card size of 3 players at card creation
- **FR-135**: System MUST forfeit bet money to the pot when a player is marked DNF after betting

**Score Verification & Fraud Prevention**
- **FR-035**: System MUST require at least one other card member to confirm scores before they become official
- **FR-036**: System MUST mark scores as "pending" until confirmed by at least one non-creator card member
- **FR-037**: System MUST prevent tag reassignment until all card scores are confirmed
- **FR-038**: System MUST allow any card member to confirm their card's scores
- **FR-039**: System MUST track who entered and who confirmed scores for audit purposes
- **FR-040**: System MUST allow league organizers (TagMasters and Assistants) to override and approve pending scores manually
- **FR-041**: System MUST allow league organizers (TagMasters and Assistants) to mark scores as disputed for investigation
- **FR-042**: System MUST maintain complete edit history for all score changes
- **FR-136**: System MUST require score confirmation from remaining non-DNF card members (excluding DNF players from confirmation count)

**Tag Assignment & Standings**
- **FR-043**: System MUST assign each registered player a unique tag number within a season (starting from Tag #1)
- **FR-044**: System MUST assign tags on first-come-first-served basis during initial registration
- **FR-045**: System MUST reassign all tags after each completed round based on round performance (best player gets Tag #1, second-best gets Tag #2, etc.)
- **FR-046**: System MUST display current tag holders and their tag numbers as the primary standings view
- **FR-047**: System MUST assign new mid-season joiners the next highest incremented tag number
- **FR-048**: System MUST enforce eligibility rules for official standings (minimum 3 completed rounds in league excluding DNF, minimum 1 round in last 5 rounds of season)
- **FR-049**: System MUST handle tie scores by awarding the better tag to the player who held the lower tag number before the round
- **FR-050**: System MUST track tag history showing which players held which tags over time
- **FR-126**: System MUST allow players to retain tags indefinitely if they don't participate in rounds (no automatic tag removal for inactivity)
- **FR-127**: System MUST exclude players from end-of-season rankings if they haven't played in the last 5 rounds/events

**Player Statistics**
- **FR-051**: System MUST provide player statistics (total rounds, average score, best score, participation rate)
- **FR-052**: System MUST calculate career statistics across all seasons and leagues
- **FR-053**: System MUST provide per-season statistical breakdowns
- **FR-054**: System MUST support real-time updates to tags and standings when rounds are completed
- **FR-055**: System MUST allow filtering statistics by season and league
- **FR-056**: System MUST track bet participation and amounts for reporting purposes (ACE pot, CTP, challenges)

**API Requirements**
- **FR-057**: System MUST provide RESTful CRUD endpoints for all entities (Users, Players, Roles, Leagues, Seasons, LeagueAssistants, Rounds, Participations, Cards, Bets, Tags, TagHistory)
- **FR-058**: System MUST generate OpenAPI/Swagger documentation for all endpoints
- **FR-059**: System MUST support pagination for list endpoints
- **FR-060**: System MUST provide comprehensive error messages with appropriate HTTP status codes
- **FR-061**: System MUST support filtering and sorting on list endpoints
- **FR-062**: System MUST validate all input data with clear validation error messages

**Monitoring & Observability**
- **FR-063**: System MUST log all API requests with timestamp, endpoint, method, status code, and response time
- **FR-064**: System MUST track API error rates and patterns across all endpoints
- **FR-065**: System MUST expose health check endpoint for service availability monitoring
- **FR-066**: System MUST provide metrics endpoint exposing request counts, error rates, and latency percentiles
- **FR-067**: System MUST send notifications when error rate exceeds configurable threshold (e.g., >5% errors in 5 minutes)
- **FR-068**: System MUST send notifications when API response time exceeds configurable threshold (e.g., >2 seconds p95)
- **FR-069**: System MUST send notifications when service health check fails
- **FR-070**: System MUST track and log unhandled exceptions with full stack traces
- **FR-071**: System MUST support configurable notification channels (email, webhook, etc.)
- **FR-072**: System MUST provide structured logging with correlation IDs for request tracing
- **FR-091**: System MUST NOT log any Personally Identifiable Information (PII) including emails, names, passwords, tokens, or IP addresses
- **FR-092**: System MUST use anonymized identifiers (user IDs, request IDs) in logs instead of PII
- **FR-093**: System MUST redact or mask sensitive fields from request/response bodies before logging
- **FR-094**: System MUST implement log sanitization to strip PII if accidentally included
- **FR-095**: System MUST document what data is considered PII and prohibited from logs
- **FR-138**: System MUST exclude PII from monitoring notifications (use anonymized IDs, error codes, not personal data)

**Participation & Attendance**
- **FR-073**: System MUST support both online pre-registration and physical check-in for rounds
- **FR-074**: System MUST require physical check-in confirmation before allowing score entry
- **FR-075**: System MUST allow players to register for rounds online before the round starts
- **FR-076**: System MUST allow TagMasters to verify and confirm physical attendance during participation recording

**Data Integrity**
- **FR-077**: System MUST prevent deletion of leagues with active seasons
- **FR-078**: System MUST prevent deletion of seasons with recorded rounds
- **FR-079**: System MUST ensure referential integrity across all entities
- **FR-080**: System MUST log all data modifications for audit purposes
- **FR-081**: System MUST track bet transactions for financial accountability
- **FR-082**: System MUST maintain accurate tag assignment history for audit purposes

**Deployment & Infrastructure**
- **FR-108**: System MUST be containerized using Docker for consistent deployment
- **FR-109**: System MUST be stateless (no local file storage, session state stored externally)
- **FR-110**: System MUST store all persistent data in external PostgreSQL database
- **FR-111**: System MUST support horizontal scaling across multiple container instances
- **FR-112**: System MUST use environment variables for all configuration (database connection, secrets, monitoring config)
- **FR-113**: System MUST include health check endpoint compatible with container orchestration platforms
- **FR-114**: System MUST log to stdout/stderr for centralized log aggregation
- **FR-115**: System MUST support graceful shutdown to complete in-flight requests before termination

### Key Entities

- **Player**: Represents a disc golf participant with an authenticated account. Key attributes include email (unique identifier), password hash, name, profile information, role assignment, and account status. Players authenticate to access the system and participate in leagues.

- **Role**: Represents permission levels within the system. Three primary roles: "Player" (standard access), "TagMaster" (league creator with full permissions), and "Assistant" (league-specific helper role with TagMaster permissions for assigned leagues). Roles determine what operations players can perform.

- **League**: Represents an organized disc golf tag competition. Key attributes include name, description, rules, organizer (TagMaster player), visibility (public/private), creation date, and status. Leagues serve as containers for seasons but don't create a hierarchy - players register for seasons independently. Private leagues require invitation or approval to join.

- **Season**: Represents a time-bound competition period within a league. Key attributes include name, start date, end date, registration open date, registration close date, associated league, and status. Players register for specific seasons to participate.

- **Round**: Represents a single disc golf game event. Key attributes include date, course name, location, creator (player), associated season, and status. Rounds are the primary gameplay tracking mechanism.

- **Card**: Represents a subset of 3-6 players who play together during a round. Key attributes include round reference, player list, and card creator. The card creator has permission to edit scores for all players in their card.

- **Participation**: Represents a player's attendance and participation lifecycle at a specific round. Key attributes include player reference, round reference, card reference, online registration timestamp, physical participation timestamp, stroke count score, and status (registered, checked_in, completed, DNF - Did Not Finish). Players can pre-register online, but physical check-in by league organizers is required before scores can be entered. This prevents remote/fraudulent score entry. Players marked as DNF are excluded from tag reassignment.

- **Tag**: Represents a player's current position/rank within a season. Key attributes include tag number (1 is best), player reference, season reference, assignment date, and status. Tags are assigned first-come-first-served at season start, then reassigned after each round based on performance. Lower tag numbers indicate better standing.

- **TagHistory**: Represents historical tag assignments over time. Key attributes include tag number, player reference, season reference, round reference, assignment date, and relinquished date. Tracks which players held which tags and when, providing an audit trail of competitive progression.

- **Bet**: Represents optional money bets/challenges that players can participate in during a round. Key attributes include bet type (ACE pot, CTP - Closest to Pin, random challenge), player reference, round reference, amount, and status. Bets are recorded during the physical participation process by league organizers (TagMasters or Assistants). System tracks participation only (no payout processing).

- **LeagueAssistant**: Represents the assignment of Assistant role to a player for a specific league. Key attributes include player reference, league reference, assigned by (TagMaster reference), assigned date, and status. Allows TagMasters to delegate league management responsibilities to trusted helpers. Assistants have same permissions as TagMasters but only for their assigned leagues.

### Assumptions

- Players can participate in multiple leagues and multiple seasons simultaneously
- Email is the primary unique identifier for players
- Scores use traditional disc golf stroke counting (lower scores are better)
- Total score only is recorded (not hole-by-hole scores)
- Tie scores are resolved by comparing pre-round tag numbers (lower tag wins)
- **Tag system is the primary competitive model**: Tags represent positional rankings (Tag #1 is best)
- Tags are reassigned after EVERY completed round based on that round's performance (not cumulative)
- Initial tag assignment is first-come-first-served during season registration
- One tag per registered player per season (tag numbers are unique within a season)
- Mid-season joiners receive next highest incremented tag number
- Eligibility for official standings requires: minimum 3 rounds in league (season-independent) AND minimum 1 round in last 5 rounds of season
- "Last 5 rounds of season" is calculated based on most recent completed rounds
- Online registration is for convenience; physical check-in confirmation is required for score entry
- Physical check-in is performed by league organizers (TagMasters or Assistants) at the course before rounds start
- Cards are created by players after physical check-in confirmation but before playing
- Card creator enters scores for all players in their card after playing
- Assistant role is league-specific (not global like TagMaster)
- TagMasters can grant and revoke Assistant privileges for their leagues
- Assistants have same permissions as TagMasters within their assigned leagues
- Assistants can create new leagues and become TagMaster for those leagues
- Deleting a league automatically removes all Assistant role assignments for that league
- Players and Rounds support soft deletion to preserve historical data
- Card size is flexible (typically 3-6 players) but enforced by API validation
- Each player can only be on one card per round
- 2-hour score confirmation window starts when scores are submitted (not when round physically ends)
- Players retain tags indefinitely even if inactive, but are excluded from end-of-season rankings if they haven't played in last 5 rounds
- Players can be removed from cards for emergencies (marked as DNF - Did Not Finish)
- DNF players are excluded from tag reassignment calculations
- DNF rounds don't count toward eligibility requirements (minimum 3 completed rounds excluding DNF)
- DNF players forfeit their bet money to the pot (no refunds)
- Once a player is marked DNF, they cannot be re-added to the card (final status)
- Minimum card size is 3 players (enforced at card creation)
- Score confirmation requires at least 1 non-creator card member (excluding DNF players from count)
- When an Assistant is removed from a league, ownership of their created data transfers to the league's TagMaster
- Monitoring notifications must exclude PII (use anonymized IDs, error codes only)
- Email verification is optional during registration
- Rate limiting is 50 requests per minute per authenticated user
- Score confirmation requires at least one non-creator card member to approve
- Score confirmation is passive (card members check app and confirm when convenient) **[FRONTEND-TODO]**
- Card creator receives pending confirmation message until scores are confirmed **[FRONTEND-TODO]**
- Unconfirmed scores have 2-hour window before round becomes stuck requiring TagMaster intervention
- Any card member can flag/dispute scores; TagMaster resolves disputes
- Course names are stored as text (no separate course entity for MVP)
- Par information for courses is out of scope for initial version
- Cards are typically 3-6 players but system should allow flexibility
- Card creator typically manages scores for their entire card (common disc golf practice)
- TagMasters perform physical check-ins at the course before rounds start
- Participation workflow captures attendance and optional bet participation in single operation
- Bet types include: ACE pot (hole-in-one pool), CTP (Closest to Pin challenge), and random challenges
- Bet tracking is for record-keeping only; payout calculation and money handling are out of scope for MVP
- System tracks bet amounts for accountability but doesn't process payments
- TagMaster collects physical bets during physical check-in and manually distributes winnings after round completion
- System tracks who participated in which bets but TagMaster handles all physical cash/money
- Private league approval workflow is asynchronous (no real-time notifications) **[FRONTEND-TODO: Polling or pull-to-refresh for approval status]**
- Career statistics span all seasons and all leagues for each player
- All dates and times are stored in UTC
- File uploads (profile pictures, course maps) are out of scope for initial version **[FRONTEND-TODO: Image picker, camera integration]**
- Real-time user notifications (in-app, push) are out of scope for initial version **[FRONTEND-TODO: iOS push notifications, in-app alerts]**
- Payment processing for bets/registration fees are out of scope for initial version
- Third-party integrations (PDGA, UDisc, etc.) are out of scope for initial version
- Mobile app development is out of scope (API only) **[FRONTEND-TODO: iOS app specification needed]**
- Monitoring notifications for API health are in scope and configurable
- Default monitoring notification channel is webhook (can extend to email)
- Application is stateless and designed for horizontal scaling
- All state is stored in PostgreSQL (no local file system dependencies)
- JWT tokens are stateless (no server-side session storage required)
- JWT tokens include expiration time and must be refreshed periodically
- Application is containerized with Docker for ECS deployment
- Container orchestration configuration (ECS task definitions, load balancers) is out of scope for MVP but API is designed to support it
- Database connection pooling handles multiple concurrent container instances
- Environment-based configuration allows different settings per deployment environment
- CORS is configurable per environment (development allows localhost, production specifies allowed origins)
- Rate limiting is applied per IP address for unauthenticated endpoints, per user for authenticated endpoints
- Password reset tokens expire after 1 hour for security
- All passwords must meet minimum complexity: 8+ characters, 1 uppercase, 1 lowercase, 1 number
- Authentication failures are logged but don't expose whether email exists (prevent user enumeration)
- Logs contain NO PII: emails, names, passwords, tokens, IP addresses are never logged
- Logs use anonymized IDs (user_id, player_id, request_id) to trace issues without exposing identity
- Request/response bodies are sanitized before logging (sensitive fields redacted)
- PII includes: email addresses, player names, passwords, authentication tokens, JWT contents, IP addresses, physical locations with identifiers
- Non-PII safe to log: user IDs, timestamps, HTTP methods, endpoints (without query params containing PII), status codes, response times, error types

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Players can complete account registration and login in under 2 minutes **[FRONTEND-TODO: UX flow]**
- **SC-002**: System handles 1000 concurrent authenticated users without performance degradation
- **SC-003**: All API endpoints respond within 500ms for standard queries (excluding complex analytics)
- **SC-004**: API documentation is automatically generated and accessible at /docs endpoint
- **SC-005**: 95% of player operations (view standings, record rounds) succeed on first attempt without errors
- **SC-006**: League organizers can create a league and season in under 5 minutes **[FRONTEND-TODO: UX flow]**
- **SC-007**: Players can view updated tag standings within 2 seconds of round finalization and tag reassignment **[FRONTEND-TODO: UI refresh]**
- **SC-008**: Tag reassignment after round completion happens automatically and completes within 5 seconds
- **SC-009**: System maintains 99.9% uptime during active season periods
- **SC-010**: All API endpoints include proper error handling with meaningful messages
- **SC-011**: Zero data loss or corruption during concurrent updates to the same season
- **SC-012**: Tag history provides complete audit trail showing all tag assignments over time

### Quality Metrics

- **SC-013**: API documentation covers 100% of endpoints with request/response examples
- **SC-014**: All endpoints properly implement REST conventions (correct HTTP methods and status codes)
- **SC-015**: Database queries are indexed and optimized (no N+1 queries, especially for tag reassignment)
- **SC-016**: All sensitive data (passwords, tokens) is properly encrypted
- **SC-017**: Code structure allows new entity types to be added without modifying existing endpoints
- **SC-018**: Tag reassignment algorithm is efficient and scales to seasons with 100+ players
- **SC-019**: API monitoring captures 100% of requests with status codes, response times, and errors
- **SC-020**: Health check endpoint responds within 100ms under normal load
- **SC-021**: Monitoring notifications trigger within 1 minute of detecting threshold violations
- **SC-022**: Application can be deployed as multiple container instances without state conflicts
- **SC-023**: Container startup time is under 30 seconds from cold start to ready state
- **SC-024**: Application handles graceful shutdown within 10 seconds, completing in-flight requests
- **SC-025**: All endpoints enforce authentication and authorization correctly (no unauthorized access)
- **SC-026**: CORS is properly configured and prevents unauthorized cross-origin requests in production
- **SC-027**: Rate limiting prevents abuse without impacting legitimate users (successful requests within limits)
- **SC-028**: Password hashing uses industry-standard algorithms (bcrypt/argon2) with proper salting
- **SC-029**: All database queries use parameterized statements or ORM (no SQL injection vulnerabilities)
- **SC-030**: Manual audit of logs confirms zero PII is present (no emails, names, passwords, tokens, IP addresses)
- **SC-031**: Log sanitization correctly redacts sensitive fields from request/response bodies before logging
