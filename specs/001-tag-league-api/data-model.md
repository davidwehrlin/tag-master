# Data Model: Disc Golf Tag League API

**Feature**: 001-tag-league-api  
**Date**: 2025-11-09  
**Status**: Complete

This document defines the complete data model for the disc golf tag league API, including all entities, fields, relationships, indexes, and validation rules.

---

## Entity Relationship Overview

```
Player (1) ──< creates >──── (M) League
Player (1) ──< registers >── (M) Season (via SeasonRegistration implicit)
Player (1) ──< has >──────── (M) Tag (one per season)
Player (1) ──< has >──────── (M) TagHistory
Player (1) ──< creates >──── (M) Round
Player (1) ──< creates >──── (M) Card
Player (1) ──< participates > (M) Participation
Player (1) ──< places >───── (M) Bet
Player (1) ──< assigned as > (M) LeagueAssistant

League (1) ──< contains >─── (M) Season
League (1) ──< has >──────── (M) LeagueAssistant

Season (1) ──< contains >─── (M) Round
Season (1) ──< has >──────── (M) Tag
Season (1) ──< has >──────── (M) TagHistory

Round (1) ──< has >───────── (M) Card
Round (1) ──< has >───────── (M) Participation
Round (1) ──< has >───────── (M) Bet
Round (1) ──< triggers >──── (M) TagHistory

Card (1) ──< contains >───── (M) Participation
```

---

## Base Model (Abstract)

All models inherit from this base to ensure consistent timestamps and soft deletion support.

```python
# app/models/base.py
from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class SoftDeleteMixin:
    """Mixin for entities that support soft deletion"""
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    @property
    def is_deleted(self):
        return self.deleted_at is not None
```

---

## Entity: Player

Represents an authenticated user account with disc golf league participation.

### SQLAlchemy Model

```python
# app/models/player.py
from sqlalchemy import Column, String, Enum, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, SoftDeleteMixin
import enum

class PlayerRole(str, enum.Enum):
    PLAYER = "Player"
    TAG_MASTER = "TagMaster"
    ASSISTANT = "Assistant"  # League-specific, tracked via LeagueAssistant

class Player(BaseModel, SoftDeleteMixin):
    __tablename__ = "players"
    
    # Fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    bio = Column(String(1000), nullable=True)
    roles = Column(ARRAY(String), nullable=False, default=["Player"])  # Can have multiple roles
    email_verified = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    created_leagues = relationship("League", back_populates="organizer", foreign_keys="League.organizer_id")
    tags = relationship("Tag", back_populates="player", cascade="all, delete-orphan")
    tag_history = relationship("TagHistory", back_populates="player", cascade="all, delete-orphan")
    participations = relationship("Participation", back_populates="player", cascade="all, delete-orphan")
    created_rounds = relationship("Round", back_populates="creator", foreign_keys="Round.creator_id")
    created_cards = relationship("Card", back_populates="creator", foreign_keys="Card.creator_id")
    bets = relationship("Bet", back_populates="player", cascade="all, delete-orphan")
    assistant_assignments = relationship("LeagueAssistant", back_populates="player", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_player_email", "email"),
        Index("idx_player_deleted", "deleted_at"),
    )
```

### Field Definitions

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique player identifier |
| `email` | String(255) | UNIQUE, NOT NULL | Player's email address (login credential) |
| `password_hash` | String(255) | NOT NULL | Bcrypt hashed password |
| `name` | String(255) | NOT NULL | Player's display name |
| `bio` | String(1000) | NULLABLE | Optional player biography |
| `roles` | String[] | NOT NULL | Array of role names (Player, TagMaster) |
| `email_verified` | Boolean | NOT NULL, DEFAULT false | Email verification status (optional in MVP) |
| `deleted_at` | DateTime(TZ) | NULLABLE, INDEXED | Soft deletion timestamp |
| `created_at` | DateTime(TZ) | NOT NULL | Account creation timestamp |
| `updated_at` | DateTime(TZ) | NOT NULL | Last modification timestamp |

### Validation Rules

- **Email**: Must be valid email format, unique across all non-deleted players
- **Password**: Minimum 8 characters, must contain uppercase, lowercase, and number (validated before hashing)
- **Name**: 2-255 characters, cannot be empty string
- **Roles**: Must contain at least "Player" role; "TagMaster" added when creating first league
- **Soft Delete**: Cannot delete if player is organizer of active leagues or has active tags

### State Transitions

1. **Registration**: `created` → `email_verified=false`
2. **Email Verification** (optional): `email_verified=false` → `email_verified=true`
3. **First League Creation**: `roles=["Player"]` → `roles=["Player", "TagMaster"]`
4. **Soft Deletion**: `deleted_at=null` → `deleted_at=<timestamp>`

---

## Entity: League

Represents an organized disc golf tag competition.

### SQLAlchemy Model

```python
# app/models/league.py
from sqlalchemy import Column, String, Text, Enum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, SoftDeleteMixin
import enum

class LeagueVisibility(str, enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"

class League(BaseModel, SoftDeleteMixin):
    __tablename__ = "leagues"
    
    # Fields
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rules = Column(Text, nullable=True)
    visibility = Column(Enum(LeagueVisibility), nullable=False, default=LeagueVisibility.PUBLIC, index=True)
    organizer_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    
    # Relationships
    organizer = relationship("Player", back_populates="created_leagues", foreign_keys=[organizer_id])
    seasons = relationship("Season", back_populates="league", cascade="all, delete-orphan")
    assistants = relationship("LeagueAssistant", back_populates="league", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_league_organizer", "organizer_id"),
        Index("idx_league_visibility", "visibility"),
        Index("idx_league_deleted", "deleted_at"),
    )
```

### Field Definitions

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique league identifier |
| `name` | String(255) | NOT NULL | League name |
| `description` | Text | NULLABLE | League description and details |
| `rules` | Text | NULLABLE | League-specific rules |
| `visibility` | Enum | NOT NULL, INDEXED | "public" or "private" |
| `organizer_id` | UUID | FOREIGN KEY, NOT NULL, INDEXED | Creator/owner player ID |
| `deleted_at` | DateTime(TZ) | NULLABLE, INDEXED | Soft deletion timestamp |
| `created_at` | DateTime(TZ) | NOT NULL | League creation timestamp |
| `updated_at` | DateTime(TZ) | NOT NULL | Last modification timestamp |

### Validation Rules

- **Name**: 3-255 characters, required
- **Organizer**: Must be valid player with TagMaster role
- **Visibility**: Must be "public" or "private"
- **Soft Delete**: Cannot delete if league has active seasons with rounds

### State Transitions

1. **Creation**: Player creates league → Player gains TagMaster role → League created with status "active"
2. **Visibility Change**: `public` ↔ `private` (any time)
3. **Soft Deletion**: `deleted_at=null` → `deleted_at=<timestamp>` (only if no active seasons)

---

## Entity: Season

Represents a time-bound competition period within a league.

### SQLAlchemy Model

```python
# app/models/season.py
from sqlalchemy import Column, String, Date, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Season(BaseModel):
    __tablename__ = "seasons"
    
    # Fields
    name = Column(String(255), nullable=False)
    league_id = Column(UUID(as_uuid=True), ForeignKey("leagues.id"), nullable=False, index=True)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    registration_open_date = Column(Date, nullable=True)
    registration_close_date = Column(Date, nullable=True)
    
    # Relationships
    league = relationship("League", back_populates="seasons")
    rounds = relationship("Round", back_populates="season", cascade="all, delete-orphan")
    tags = relationship("Tag", back_populates="season", cascade="all, delete-orphan")
    tag_history = relationship("TagHistory", back_populates="season", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_season_league", "league_id"),
        Index("idx_season_dates", "start_date", "end_date"),
    )
```

### Field Definitions

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique season identifier |
| `name` | String(255) | NOT NULL | Season name (e.g., "Spring 2025") |
| `league_id` | UUID | FOREIGN KEY, NOT NULL, INDEXED | Parent league ID |
| `start_date` | Date | NOT NULL, INDEXED | Season start date |
| `end_date` | Date | NOT NULL, INDEXED | Season end date |
| `registration_open_date` | Date | NULLABLE | Registration opens (optional, can be anytime) |
| `registration_close_date` | Date | NULLABLE | Registration closes (optional, can be anytime) |
| `created_at` | DateTime(TZ) | NOT NULL | Season creation timestamp |
| `updated_at` | DateTime(TZ) | NOT NULL | Last modification timestamp |

### Validation Rules

- **Name**: 3-255 characters, required
- **Dates**: `end_date` must be after `start_date`
- **Registration Dates**: If provided, `registration_close_date` must be after `registration_open_date`
- **League**: Must reference valid non-deleted league

### State Transitions

1. **Creation**: Season created → Open for registration
2. **Active**: `current_date >= start_date AND current_date <= end_date`
3. **Completed**: `current_date > end_date` (eligibility rules apply)

---

## Entity: LeagueAssistant

Represents league-specific assistant role assignments.

### SQLAlchemy Model

```python
# app/models/league_assistant.py
from sqlalchemy import Column, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class LeagueAssistant(BaseModel):
    __tablename__ = "league_assistants"
    
    # Fields
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    league_id = Column(UUID(as_uuid=True), ForeignKey("leagues.id"), nullable=False, index=True)
    assigned_by_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False)
    
    # Relationships
    player = relationship("Player", back_populates="assistant_assignments", foreign_keys=[player_id])
    league = relationship("League", back_populates="assistants")
    assigned_by = relationship("Player", foreign_keys=[assigned_by_id])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("player_id", "league_id", name="uq_league_assistant"),
        Index("idx_assistant_player", "player_id"),
        Index("idx_assistant_league", "league_id"),
    )
```

### Field Definitions

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique assignment identifier |
| `player_id` | UUID | FOREIGN KEY, NOT NULL, INDEXED | Assistant player ID |
| `league_id` | UUID | FOREIGN KEY, NOT NULL, INDEXED | League ID |
| `assigned_by_id` | UUID | FOREIGN KEY, NOT NULL | TagMaster who assigned this assistant |
| `created_at` | DateTime(TZ) | NOT NULL | Assignment timestamp |
| `updated_at` | DateTime(TZ) | NOT NULL | Last modification timestamp |

### Validation Rules

- **Unique Constraint**: One player can only be assistant for same league once
- **Assigner**: Must be TagMaster or league organizer
- **Player**: Must be valid non-deleted player

### State Transitions

1. **Assignment**: TagMaster assigns player → LeagueAssistant record created
2. **Revocation**: TagMaster removes assistant → LeagueAssistant record deleted
3. **League Deletion**: League deleted → All LeagueAssistant records automatically deleted (cascade)

---

## Entity: Round

Represents a single disc golf game event.

### SQLAlchemy Model

```python
# app/models/round.py
from sqlalchemy import Column, String, Date, Time, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel, SoftDeleteMixin

class Round(BaseModel, SoftDeleteMixin):
    __tablename__ = "rounds"
    
    # Fields
    season_id = Column(UUID(as_uuid=True), ForeignKey("seasons.id"), nullable=False, index=True)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    course_name = Column(String(255), nullable=False)
    location = Column(String(500), nullable=True)
    start_time = Column(Time, nullable=True)
    
    # Relationships
    season = relationship("Season", back_populates="rounds")
    creator = relationship("Player", back_populates="created_rounds", foreign_keys=[creator_id])
    cards = relationship("Card", back_populates="round", cascade="all, delete-orphan")
    participations = relationship("Participation", back_populates="round", cascade="all, delete-orphan")
    bets = relationship("Bet", back_populates="round", cascade="all, delete-orphan")
    tag_history = relationship("TagHistory", back_populates="round")
    
    # Indexes
    __table_args__ = (
        Index("idx_round_season", "season_id"),
        Index("idx_round_date", "date"),
        Index("idx_round_deleted", "deleted_at"),
    )
```

### Field Definitions

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique round identifier |
| `season_id` | UUID | FOREIGN KEY, NOT NULL, INDEXED | Parent season ID |
| `creator_id` | UUID | FOREIGN KEY, NOT NULL, INDEXED | TagMaster/Assistant who created round |
| `date` | Date | NOT NULL, INDEXED | Round date |
| `course_name` | String(255) | NOT NULL | Course name (text, no separate course entity) |
| `location` | String(500) | NULLABLE | Course location/address |
| `start_time` | Time | NULLABLE | Scheduled start time |
| `deleted_at` | DateTime(TZ) | NULLABLE, INDEXED | Soft deletion timestamp |
| `created_at` | DateTime(TZ) | NOT NULL | Round creation timestamp |
| `updated_at` | DateTime(TZ) | NOT NULL | Last modification timestamp |

### Validation Rules

- **Season**: Must reference valid season
- **Creator**: Must be TagMaster or Assistant for league
- **Date**: Cannot be in distant past (e.g., >1 year ago)
- **Course Name**: 3-255 characters, required
- **Soft Delete**: Preserves historical data including tag history

### State Transitions

1. **Creation**: Round created → Open for online registration
2. **Participation Phase**: Physical check-ins recorded by TagMaster/Assistant
3. **Card Formation**: Players create cards from checked-in list
4. **Scoring**: Card creators enter scores
5. **Confirmation**: Card members confirm scores (2-hour window)
6. **Finalization**: All scores confirmed → Tag reassignment triggered
7. **Soft Deletion**: `deleted_at=null` → `deleted_at=<timestamp>` (preserves history)

---

## Entity: Card

Represents a group of 3-6 players who play together during a round.

### SQLAlchemy Model

```python
# app/models/card.py
from sqlalchemy import Column, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Card(BaseModel):
    __tablename__ = "cards"
    
    # Fields
    round_id = Column(UUID(as_uuid=True), ForeignKey("rounds.id"), nullable=False, index=True)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    
    # Relationships
    round = relationship("Round", back_populates="cards")
    creator = relationship("Player", back_populates="created_cards", foreign_keys=[creator_id])
    participations = relationship("Participation", back_populates="card")
    
    # Indexes
    __table_args__ = (
        Index("idx_card_round", "round_id"),
        Index("idx_card_creator", "creator_id"),
    )
```

### Field Definitions

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique card identifier |
| `round_id` | UUID | FOREIGN KEY, NOT NULL, INDEXED | Parent round ID |
| `creator_id` | UUID | FOREIGN KEY, NOT NULL, INDEXED | Player who created the card |
| `created_at` | DateTime(TZ) | NOT NULL | Card creation timestamp |
| `updated_at` | DateTime(TZ) | NOT NULL | Last modification timestamp |

### Validation Rules

- **Round**: Must reference valid non-deleted round
- **Creator**: Must be checked in to the round
- **Minimum Size**: Card must have at least 3 players (enforced via participation count)
- **Typical Size**: 3-6 players (soft limit, flexible)
- **Player Uniqueness**: Each player can only be on one card per round

### State Transitions

1. **Creation**: Card created by checked-in player
2. **Player Assignment**: Players added to card (via Participation.card_id)
3. **Scoring**: Card creator enters scores for all players
4. **Confirmation**: Other card members confirm scores

---

## Entity: Participation

Represents a player's attendance and participation in a round.

### SQLAlchemy Model

```python
# app/models/participation.py
from sqlalchemy import Column, Integer, ForeignKey, Enum, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum

class ParticipationStatus(str, enum.Enum):
    REGISTERED = "registered"      # Online pre-registration
    CHECKED_IN = "checked_in"      # Physical check-in confirmed
    COMPLETED = "completed"        # Round played, score entered
    DNF = "dnf"                    # Did Not Finish

class Participation(BaseModel):
    __tablename__ = "participations"
    
    # Fields
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    round_id = Column(UUID(as_uuid=True), ForeignKey("rounds.id"), nullable=False, index=True)
    card_id = Column(UUID(as_uuid=True), ForeignKey("cards.id"), nullable=True, index=True)
    status = Column(Enum(ParticipationStatus), nullable=False, default=ParticipationStatus.REGISTERED, index=True)
    online_registration_time = Column(DateTime(timezone=True), nullable=True)
    physical_checkin_time = Column(DateTime(timezone=True), nullable=True)
    score = Column(Integer, nullable=True)  # Stroke count (lower is better)
    score_entered_by_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=True)
    score_entered_at = Column(DateTime(timezone=True), nullable=True)
    score_confirmed = Column(Boolean, default=False, nullable=False)
    score_confirmed_by_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=True)
    score_confirmed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    player = relationship("Player", back_populates="participations", foreign_keys=[player_id])
    round = relationship("Round", back_populates="participations")
    card = relationship("Card", back_populates="participations")
    score_entered_by = relationship("Player", foreign_keys=[score_entered_by_id])
    score_confirmed_by = relationship("Player", foreign_keys=[score_confirmed_by_id])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("player_id", "round_id", name="uq_participation_player_round"),
        Index("idx_participation_player", "player_id"),
        Index("idx_participation_round", "round_id"),
        Index("idx_participation_card", "card_id"),
        Index("idx_participation_status", "status"),
    )
```

### Field Definitions

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique participation identifier |
| `player_id` | UUID | FOREIGN KEY, NOT NULL, INDEXED | Player ID |
| `round_id` | UUID | FOREIGN KEY, NOT NULL, INDEXED | Round ID |
| `card_id` | UUID | FOREIGN KEY, NULLABLE, INDEXED | Card ID (assigned after physical checkin) |
| `status` | Enum | NOT NULL, INDEXED | "registered", "checked_in", "completed", "dnf" |
| `online_registration_time` | DateTime(TZ) | NULLABLE | Online pre-registration timestamp |
| `physical_checkin_time` | DateTime(TZ) | NULLABLE | Physical check-in timestamp |
| `score` | Integer | NULLABLE | Stroke count (lower is better) |
| `score_entered_by_id` | UUID | FOREIGN KEY, NULLABLE | Who entered the score (usually card creator) |
| `score_entered_at` | DateTime(TZ) | NULLABLE | When score was entered |
| `score_confirmed` | Boolean | NOT NULL, DEFAULT false | Score confirmation status |
| `score_confirmed_by_id` | UUID | FOREIGN KEY, NULLABLE | Who confirmed the score |
| `score_confirmed_at` | DateTime(TZ) | NULLABLE | When score was confirmed |
| `created_at` | DateTime(TZ) | NOT NULL | Participation creation timestamp |
| `updated_at` | DateTime(TZ) | NOT NULL | Last modification timestamp |

### Validation Rules

- **Unique Constraint**: One player can only participate once per round
- **Card Assignment**: Can only be assigned to card after physical check-in
- **Score Entry**: Can only enter score if `status="checked_in"` (not just "registered")
- **Score Confirmation**: Cannot confirm own score (must be different card member)
- **DNF**: Once marked DNF, cannot be changed back to completed

### State Transitions

1. **Online Registration**: `status="registered"`, `online_registration_time` set
2. **Physical Check-in**: `status="checked_in"`, `physical_checkin_time` set by TagMaster/Assistant
3. **Card Assignment**: `card_id` assigned when player joins/creates card
4. **Score Entry**: `status="completed"`, `score` entered, `score_entered_by_id` and `score_entered_at` set
5. **Score Confirmation**: `score_confirmed=true`, `score_confirmed_by_id` and `score_confirmed_at` set
6. **DNF (Abandonment)**: `status="dnf"` (final state, excluded from tag reassignment)

---

## Entity: Bet

Represents optional money bets/challenges during a round.

### SQLAlchemy Model

```python
# app/models/bet.py
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Index
from sqlalchemy.dialects.postgresql import UUID, NUMERIC
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum

class BetType(str, enum.Enum):
    ACE_POT = "ace_pot"          # Hole-in-one pool
    CTP = "ctp"                  # Closest to Pin
    CHALLENGE = "challenge"       # Random challenges

class Bet(BaseModel):
    __tablename__ = "bets"
    
    # Fields
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    round_id = Column(UUID(as_uuid=True), ForeignKey("rounds.id"), nullable=False, index=True)
    bet_type = Column(Enum(BetType), nullable=False, index=True)
    amount = Column(NUMERIC(10, 2), nullable=False)  # Decimal for currency
    description = Column(String(500), nullable=True)
    
    # Relationships
    player = relationship("Player", back_populates="bets")
    round = relationship("Round", back_populates="bets")
    
    # Indexes
    __table_args__ = (
        Index("idx_bet_player", "player_id"),
        Index("idx_bet_round", "round_id"),
        Index("idx_bet_type", "bet_type"),
    )
```

### Field Definitions

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique bet identifier |
| `player_id` | UUID | FOREIGN KEY, NOT NULL, INDEXED | Player ID |
| `round_id` | UUID | FOREIGN KEY, NOT NULL, INDEXED | Round ID |
| `bet_type` | Enum | NOT NULL, INDEXED | "ace_pot", "ctp", "challenge" |
| `amount` | Numeric(10,2) | NOT NULL | Bet amount (currency) |
| `description` | String(500) | NULLABLE | Optional bet description |
| `created_at` | DateTime(TZ) | NOT NULL | Bet creation timestamp (during check-in) |
| `updated_at` | DateTime(TZ) | NOT NULL | Last modification timestamp |

### Validation Rules

- **Amount**: Must be positive (> 0)
- **Bet Type**: Must be one of ace_pot, ctp, challenge
- **Round**: Must reference valid round
- **Player**: Must be checked in to round (physical check-in)

### State Transitions

1. **Creation**: Bet recorded during physical check-in by TagMaster/Assistant
2. **DNF Forfeit**: If player marked DNF → Bet money forfeited to pot (handled externally)

**Note**: Payout calculation and money handling are out of scope. This entity tracks participation only.

---

## Entity: Tag

Represents a player's current position/rank within a season.

### SQLAlchemy Model

```python
# app/models/tag.py
from sqlalchemy import Column, Integer, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Tag(BaseModel):
    __tablename__ = "tags"
    
    # Fields
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    season_id = Column(UUID(as_uuid=True), ForeignKey("seasons.id"), nullable=False, index=True)
    tag_number = Column(Integer, nullable=False)  # 1 is best
    assignment_date = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    player = relationship("Player", back_populates="tags")
    season = relationship("Season", back_populates="tags")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("player_id", "season_id", name="uq_tag_player_season"),
        UniqueConstraint("season_id", "tag_number", name="uq_tag_season_number"),
        Index("idx_tag_player", "player_id"),
        Index("idx_tag_season", "season_id"),
        Index("idx_tag_season_number", "season_id", "tag_number"),
    )
```

### Field Definitions

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique tag identifier |
| `player_id` | UUID | FOREIGN KEY, NOT NULL, INDEXED | Player ID |
| `season_id` | UUID | FOREIGN KEY, NOT NULL, INDEXED | Season ID |
| `tag_number` | Integer | NOT NULL | Tag position (1 is best, lower is better) |
| `assignment_date` | DateTime(TZ) | NOT NULL | When tag was assigned/updated |
| `created_at` | DateTime(TZ) | NOT NULL | Tag creation timestamp |
| `updated_at` | DateTime(TZ) | NOT NULL | Last modification timestamp |

### Validation Rules

- **Unique Constraint 1**: One player has exactly one tag per season
- **Unique Constraint 2**: Each tag number is unique within a season
- **Tag Number**: Must be positive integer (≥ 1)
- **Assignment**: Tag number reassigned after each completed round

### State Transitions

1. **Initial Assignment**: Player registers → Receives next available tag number (first-come-first-served)
2. **Round Completion**: All players' tags reassigned based on round performance (best score gets Tag #1)
3. **Mid-Season Join**: Player registers → Receives next highest incremented tag number
4. **Inactivity**: Player keeps tag indefinitely (no automatic removal for inactivity)

---

## Entity: TagHistory

Represents historical tag assignments over time (audit trail).

### SQLAlchemy Model

```python
# app/models/tag_history.py
from sqlalchemy import Column, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class TagHistory(BaseModel):
    __tablename__ = "tag_history"
    
    # Fields
    tag_number = Column(Integer, nullable=False)
    player_id = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False, index=True)
    season_id = Column(UUID(as_uuid=True), ForeignKey("seasons.id"), nullable=False, index=True)
    round_id = Column(UUID(as_uuid=True), ForeignKey("rounds.id"), nullable=True, index=True)
    assignment_date = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    player = relationship("Player", back_populates="tag_history")
    season = relationship("Season", back_populates="tag_history")
    round = relationship("Round", back_populates="tag_history")
    
    # Indexes
    __table_args__ = (
        Index("idx_tag_history_player", "player_id"),
        Index("idx_tag_history_season", "season_id"),
        Index("idx_tag_history_round", "round_id"),
        Index("idx_tag_history_player_season", "player_id", "season_id"),
        Index("idx_tag_history_assignment_date", "assignment_date"),
    )
```

### Field Definitions

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique history record identifier |
| `tag_number` | Integer | NOT NULL | Tag number at this point in time |
| `player_id` | UUID | FOREIGN KEY, NOT NULL, INDEXED | Player ID |
| `season_id` | UUID | FOREIGN KEY, NOT NULL, INDEXED | Season ID |
| `round_id` | UUID | FOREIGN KEY, NULLABLE, INDEXED | Round that triggered this assignment (null for initial) |
| `assignment_date` | DateTime(TZ) | NOT NULL, INDEXED | When tag was assigned |
| `created_at` | DateTime(TZ) | NOT NULL | Record creation timestamp |
| `updated_at` | DateTime(TZ) | NOT NULL | Last modification timestamp |

### Validation Rules

- **Tag Number**: Must be positive integer (≥ 1)
- **Round**: Can be null for initial registration, must exist for reassignments
- **Immutable**: History records are never updated or deleted (append-only)

### State Transitions

1. **Initial Registration**: Record created with `round_id=null` when player first registers for season
2. **Round Completion**: New record created after each round showing new tag assignment
3. **Audit Trail**: Provides complete history of tag movements over time

---

## Indexes Summary

### Critical Performance Indexes

| Table | Index | Columns | Purpose |
|-------|-------|---------|---------|
| `players` | `idx_player_email` | `email` | Login lookup |
| `players` | `idx_player_deleted` | `deleted_at` | Filter active players |
| `leagues` | `idx_league_organizer` | `organizer_id` | Find leagues by organizer |
| `leagues` | `idx_league_visibility` | `visibility` | Filter public/private leagues |
| `seasons` | `idx_season_league` | `league_id` | Find seasons by league |
| `seasons` | `idx_season_dates` | `start_date, end_date` | Find active seasons |
| `rounds` | `idx_round_season` | `season_id` | Find rounds by season |
| `rounds` | `idx_round_date` | `date` | Sort/filter rounds by date |
| `participations` | `uq_participation_player_round` | `player_id, round_id` | Prevent duplicate participations |
| `participations` | `idx_participation_status` | `status` | Filter by participation status |
| `cards` | `idx_card_round` | `round_id` | Find cards by round |
| `tags` | `uq_tag_player_season` | `player_id, season_id` | One tag per player per season |
| `tags` | `uq_tag_season_number` | `season_id, tag_number` | Unique tag numbers in season |
| `tags` | `idx_tag_season_number` | `season_id, tag_number` | Standings queries (sorted by tag) |
| `tag_history` | `idx_tag_history_player_season` | `player_id, season_id` | Player tag progression |
| `league_assistants` | `uq_league_assistant` | `player_id, league_id` | One assistant assignment per league |

---

## Relationships Summary

### One-to-Many Relationships

- Player → Leagues (organizer)
- Player → Tags (current tags)
- Player → TagHistory (historical tags)
- Player → Participations
- Player → Rounds (creator)
- Player → Cards (creator)
- Player → Bets
- Player → LeagueAssistants (assistant assignments)
- League → Seasons
- League → LeagueAssistants
- Season → Rounds
- Season → Tags
- Season → TagHistory
- Round → Cards
- Round → Participations
- Round → Bets
- Round → TagHistory
- Card → Participations

### Cascade Delete Rules

- **Player deleted** → Soft delete only (preserve historical data)
- **League deleted** → Cascade to Seasons and LeagueAssistants
- **Season deleted** → Cascade to Rounds, Tags, TagHistory
- **Round deleted** → Soft delete only (preserve Tag history)
- **Card deleted** → Update Participation.card_id to null

---

## Data Model Validation Queries

### Check Tag Uniqueness in Season

```sql
SELECT season_id, tag_number, COUNT(*)
FROM tags
GROUP BY season_id, tag_number
HAVING COUNT(*) > 1;
-- Should return 0 rows
```

### Check Player Can Only Be on One Card Per Round

```sql
SELECT player_id, round_id, COUNT(DISTINCT card_id)
FROM participations
WHERE card_id IS NOT NULL
GROUP BY player_id, round_id
HAVING COUNT(DISTINCT card_id) > 1;
-- Should return 0 rows
```

### Check Eligibility Requirements

```sql
-- Players with minimum 3 completed rounds in league (season-independent)
SELECT p.id, p.name, l.id as league_id, COUNT(DISTINCT part.id) as completed_rounds
FROM players p
JOIN participations part ON p.id = part.player_id
JOIN rounds r ON part.round_id = r.id
JOIN seasons s ON r.season_id = s.id
JOIN leagues l ON s.league_id = l.id
WHERE part.status = 'completed'  -- Exclude DNF
GROUP BY p.id, p.name, l.id
HAVING COUNT(DISTINCT part.id) >= 3;
```

### Check Score Confirmation Status

```sql
-- Rounds with pending score confirmations
SELECT r.id, r.date, r.course_name,
       COUNT(part.id) FILTER (WHERE part.score IS NOT NULL AND NOT part.score_confirmed) as pending_confirmations
FROM rounds r
LEFT JOIN participations part ON r.id = part.round_id
GROUP BY r.id, r.date, r.course_name
HAVING COUNT(part.id) FILTER (WHERE part.score IS NOT NULL AND NOT part.score_confirmed) > 0;
```

---

## Migration Strategy

### Alembic Migration Order

1. Create `players` table (base entity)
2. Create `leagues` table (references players)
3. Create `seasons` table (references leagues)
4. Create `league_assistants` table (references players and leagues)
5. Create `rounds` table (references seasons and players)
6. Create `cards` table (references rounds and players)
7. Create `participations` table (references players, rounds, cards)
8. Create `bets` table (references players and rounds)
9. Create `tags` table (references players and seasons)
10. Create `tag_history` table (references players, seasons, rounds)

### Sample Migration (Players Table)

```python
# alembic/versions/001_create_players_table.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY

def upgrade():
    op.create_table(
        'players',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('bio', sa.String(1000), nullable=True),
        sa.Column('roles', ARRAY(sa.String), nullable=False),
        sa.Column('email_verified', sa.Boolean, nullable=False, default=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    op.create_index('idx_player_email', 'players', ['email'])
    op.create_index('idx_player_deleted', 'players', ['deleted_at'])

def downgrade():
    op.drop_index('idx_player_deleted')
    op.drop_index('idx_player_email')
    op.drop_table('players')
```

---

## Summary

This data model provides:

✅ **13 entities** with complete field definitions and relationships  
✅ **Soft deletion** for Players and Rounds (preserve historical data)  
✅ **Comprehensive indexing** for performance (email lookups, standings queries, tag reassignment)  
✅ **Audit trail** via TagHistory (complete tag movement tracking)  
✅ **Referential integrity** via foreign keys and unique constraints  
✅ **Fraud prevention** via score confirmation workflow (Participation entity)  
✅ **Eligibility tracking** via Participation status (completed vs DNF)  
✅ **Role-based access** via Player.roles and LeagueAssistant entity  

**Next Steps**: Generate API contracts (OpenAPI spec) mapping these entities to REST endpoints.
