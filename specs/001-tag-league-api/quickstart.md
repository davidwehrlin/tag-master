# Quickstart Guide: Disc Golf Tag League API

**Feature**: 001-tag-league-api  
**Date**: 2025-11-09

This guide will help you set up and run the Disc Golf Tag League API locally for development.

---

## Prerequisites

- Docker Desktop 20.10+ (recommended for easiest setup)
- Docker Compose 2.0+
- Git
- Python 3.11+ (optional, for local development without Docker)
- PostgreSQL 15+ (optional, for local development without Docker)

**Note**: All backend API code is located in the `backend/` folder at the repository root. This structure allows for future frontend addition while keeping backend isolated.

---

## Quick Start (Docker Compose - Recommended)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd TagMaster  # Repository root

### 2. Create Environment File

Create `.env` file in the project root:

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://tagmaster:dev_password@db:5432/tagmaster_dev

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Rate Limiting
RATE_LIMIT_PER_MINUTE=50

# Monitoring (optional)
MONITORING_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Environment
ENVIRONMENT=development
```

### 3. Start Services

```bash
docker-compose up -d
```

This will start:
- **PostgreSQL database** on port `5432`
- **FastAPI application** on port `8000`

### 4. Verify Services

Check that services are running:

```bash
docker-compose ps
```

Expected output:
```
NAME                COMMAND                  SERVICE   STATUS    PORTS
tagmaster-api-1     "uvicorn app.main:..."   api       running   0.0.0.0:8000->8000/tcp
tagmaster-db-1      "docker-entrypoint..."   db        running   0.0.0.0:5432->5432/tcp
```

### 3. Access the API

Backend API runs from `backend/` folder:

- **API Base URL**: http://localhost:8000
- **Swagger UI (Interactive Docs)**: http://localhost:8000/docs
- **ReDoc (Alternative Docs)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### 6. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Register a new player
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123",
    "name": "Test Player"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123"
  }'
```

---

## Local Development (Without Docker)

### 1. Install PostgreSQL

**macOS** (using Homebrew):
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install postgresql-15
sudo systemctl start postgresql
```

### 2. Create Database

```bash
# Connect to PostgreSQL
psql postgres

# Create user and database
CREATE USER tagmaster WITH PASSWORD 'dev_password';
CREATE DATABASE tagmaster_dev OWNER tagmaster;
\q
```

### 2. Setup Python Environment

```bash
# Navigate to backend folder
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Create Environment File

```bash
# From backend/ folder
cp .env.example .env
nano .env  # Edit with your database credentials
```

### 4. Run Database Migrations

```bash
# From backend/ folder (with venv activated)
alembic upgrade head
```

### 5. Start the API Server

```bash
# From backend/ folder (with venv activated)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Database Migrations

All Alembic commands run from `backend/` folder.

### Create a New Migration

```bash
# From backend/ folder
alembic revision --autogenerate -m "description of change"

# Example: Add new column  
alembic revision --autogenerate -m "add phone to players"
```

### Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade <revision_id>

# Rollback one migration
alembic downgrade -1

# Rollback to specific migration
alembic downgrade <revision_id>
```

### View Migration History

```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic show
```

---

## Running Tests

All pytest commands run from `backend/` folder.

### Setup Test Database

```bash
# Create separate test database
psql -U postgres -c "CREATE DATABASE tagmaster_test;"
```

### Run All Tests

```bash
# From backend/ folder
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_players.py

# Run specific test
pytest tests/test_players.py::test_create_player

# Run tests by marker
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m contract      # Contract tests only
```

### Generate Coverage Report

```bash
# Run tests with coverage
pytest --cov=app --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

---

## Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | - | Yes |
| `JWT_SECRET_KEY` | Secret key for JWT signing | - | Yes |
| `JWT_ALGORITHM` | JWT algorithm | HS256 | No |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time (minutes) | 1440 | No |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | - | Yes |
| `RATE_LIMIT_PER_MINUTE` | Max requests per minute per user | 50 | No |
| `MONITORING_WEBHOOK_URL` | Webhook URL for monitoring alerts | - | No |
| `ENVIRONMENT` | Environment name | development | No |

---

## Common Tasks

All commands run from repository root unless otherwise noted.

### Reset Database

**Warning**: This will delete all data!

```bash
# From repository root
# Using Docker Compose
docker-compose down -v  # Removes volumes
docker-compose up -d

# Local development (from backend/ folder)
psql postgres -c "DROP DATABASE tagmaster_dev;"
psql postgres -c "CREATE DATABASE tagmaster_dev OWNER tagmaster;"
cd backend
alembic upgrade head
```

### View Logs

```bash
# View API logs (Docker)
docker-compose logs -f api

# View database logs (Docker)
docker-compose logs -f db

# View all logs
docker-compose logs -f
```

### Access Database

```bash
# Using Docker Compose
docker-compose exec db psql -U tagmaster -d tagmaster_dev

# Local development
psql -U tagmaster -d tagmaster_dev
```

### Stop Services

```bash
# Stop services (preserve data)
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes (deletes data)
docker-compose down -v
```

---

## API Usage Examples

### 1. Register a Player

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "player@example.com",
    "password": "SecurePass123",
    "name": "John Doe",
    "bio": "Disc golf enthusiast"
  }'
```

Response:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "player@example.com",
  "name": "John Doe",
  "bio": "Disc golf enthusiast",
  "roles": ["Player"],
  "email_verified": false,
  "created_at": "2025-11-09T10:30:00Z",
  "updated_at": "2025-11-09T10:30:00Z"
}
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "player@example.com",
    "password": "SecurePass123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

Save the `access_token` for subsequent requests.

### 3. Create a League

```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X POST http://localhost:8000/api/v1/leagues \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Saturday Morning Tag League",
    "description": "Competitive tag league for experienced players",
    "rules": "PDGA rules apply. Minimum 3 rounds for eligibility.",
    "visibility": "public"
  }'
```

Response:
```json
{
  "id": "223e4567-e89b-12d3-a456-426614174001",
  "name": "Saturday Morning Tag League",
  "description": "Competitive tag league for experienced players",
  "rules": "PDGA rules apply. Minimum 3 rounds for eligibility.",
  "visibility": "public",
  "organizer_id": "123e4567-e89b-12d3-a456-426614174000",
  "created_at": "2025-11-09T10:35:00Z",
  "updated_at": "2025-11-09T10:35:00Z"
}
```

Note: Creating a league automatically grants you the `TagMaster` role.

### 4. Create a Season

```bash
curl -X POST http://localhost:8000/api/v1/seasons \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Spring 2025",
    "league_id": "223e4567-e89b-12d3-a456-426614174001",
    "start_date": "2025-03-01",
    "end_date": "2025-05-31"
  }'
```

### 5. Register for a Season

```bash
curl -X POST http://localhost:8000/api/v1/seasons/323e4567-e89b-12d3-a456-426614174002/register \
  -H "Authorization: Bearer $TOKEN"
```

Response: You receive a `Tag` with a tag number (first-come-first-served).

### 6. Create a Round

```bash
curl -X POST http://localhost:8000/api/v1/rounds \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "season_id": "323e4567-e89b-12d3-a456-426614174002",
    "date": "2025-03-15",
    "course_name": "Morley Field",
    "location": "San Diego, CA",
    "start_time": "09:00:00"
  }'
```

### 7. Physical Participation (TagMaster/Assistant only)

```bash
curl -X POST http://localhost:8000/api/v1/rounds/423e4567-e89b-12d3-a456-426614174003/participations/physical \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "player_id": "123e4567-e89b-12d3-a456-426614174000",
    "bet_participations": [
      {
        "bet_type": "ace_pot",
        "amount": 5.00
      }
    ]
  }'
```

### 8. Create a Card

```bash
curl -X POST http://localhost:8000/api/v1/cards \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "round_id": "423e4567-e89b-12d3-a456-426614174003",
    "player_ids": [
      "123e4567-e89b-12d3-a456-426614174000",
      "223e4567-e89b-12d3-a456-426614174001",
      "323e4567-e89b-12d3-a456-426614174002"
    ]
  }'
```

### 9. Enter Scores

```bash
curl -X POST http://localhost:8000/api/v1/cards/523e4567-e89b-12d3-a456-426614174004/scores \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "scores": [
      {"player_id": "123e4567-e89b-12d3-a456-426614174000", "score": 65},
      {"player_id": "223e4567-e89b-12d3-a456-426614174001", "score": 70},
      {"player_id": "323e4567-e89b-12d3-a456-426614174002", "score": 60}
    ]
  }'
```

### 10. Confirm Scores

```bash
# As a different card member (not the card creator)
curl -X POST http://localhost:8000/api/v1/cards/523e4567-e89b-12d3-a456-426614174004/scores/confirm \
  -H "Authorization: Bearer $OTHER_PLAYER_TOKEN"
```

After confirmation, tags are automatically reassigned based on round performance.

### 11. View Tag Standings

```bash
curl -X GET http://localhost:8000/api/v1/seasons/323e4567-e89b-12d3-a456-426614174002/tags \
  -H "Authorization: Bearer $TOKEN"
```

Response:
```json
{
  "items": [
    {
      "id": "...",
      "player_id": "323e4567-e89b-12d3-a456-426614174002",
      "player": {"name": "Player C", ...},
      "season_id": "323e4567-e89b-12d3-a456-426614174002",
      "tag_number": 1,
      "assignment_date": "2025-03-15T14:30:00Z",
      "is_eligible": true
    },
    ...
  ],
  "total": 10,
  "page": 1,
  "size": 20,
  "pages": 1
}
```

---

## Development Workflow

### 1. Feature Development

```bash
# 1. Create feature branch
git checkout -b feature/add-player-stats

# 2. Make changes to code

# 3. Run tests
pytest

# 4. Check code quality (optional)
flake8 app/
black app/ --check
mypy app/

# 5. Commit changes
git add .
git commit -m "Add player statistics endpoint"

# 6. Push branch
git push origin feature/add-player-stats
```

### 2. Database Schema Changes

```bash
# 1. Modify models in app/models/

# 2. Generate migration
alembic revision --autogenerate -m "Add phone number to players"

# 3. Review generated migration in alembic/versions/

# 4. Apply migration
alembic upgrade head

# 5. Test changes
pytest

# 6. Commit migration file
git add alembic/versions/
git commit -m "Add phone number to players schema"
```

### Adding New Endpoints

```bash
# All paths relative to backend/ folder:
# 1. Define Pydantic schemas in backend/app/schemas/
# 2. Create route handler in backend/app/api/v1/
# 3. Implement business logic in backend/app/services/
# 4. Write tests in backend/tests/contract/ and backend/tests/integration/
```

---

## Troubleshooting

### Database Connection Error

**Error**: `asyncpg.exceptions.InvalidCatalogNameError: database "tagmaster_dev" does not exist`

**Solution**:
```bash
# Create database
psql postgres -c "CREATE DATABASE tagmaster_dev OWNER tagmaster;"
```

### Port Already in Use

**Error**: `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution**:
```bash
# Find process using port
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process or change port in docker-compose.yml
```

### Database Migration Failed

**Error**: `alembic.util.exc.CommandError: Can't locate revision identified by 'xyz'`

**Solution**:
```bash
# Reset alembic version table
psql -U tagmaster -d tagmaster_dev -c "TRUNCATE alembic_version;"

# Stamp database with current version
alembic stamp head
```

### JWT Token Expired

**Error**: `401 Unauthorized: Token has expired`

**Solution**: Login again to get a new token. Tokens expire after 24 hours by default.

---

## Production Deployment (ECS)

### 1. Build Docker Image

```bash
# From repository root
# Build production image (Dockerfile is in backend/)
docker build -t tagmaster-api:latest -f backend/Dockerfile backend/

# Tag for ECR
docker tag tagmaster-api:latest <account-id>.dkr.ecr.<region>.amazonaws.com/tagmaster-api:latest

# Push to ECR
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/tagmaster-api:latest
```

### 2. Environment Variables (ECS Task Definition)

```json
{
  "name": "tagmaster-api",
  "image": "<account-id>.dkr.ecr.<region>.amazonaws.com/tagmaster-api:latest",
  "environment": [
    {"name": "DATABASE_URL", "value": "postgresql+asyncpg://..."},
    {"name": "JWT_SECRET_KEY", "value": "..."},
    {"name": "CORS_ORIGINS", "value": "https://app.tagmaster.com"},
    {"name": "ENVIRONMENT", "value": "production"}
  ],
  "secrets": [
    {"name": "DATABASE_PASSWORD", "valueFrom": "arn:aws:secretsmanager:..."}
  ],
  "portMappings": [
    {"containerPort": 8000, "protocol": "tcp"}
  ],
  "healthCheck": {
    "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
    "interval": 30,
    "timeout": 5,
    "retries": 3,
    "startPeriod": 10
  }
}
```

### 3. Run Database Migrations

```bash
# One-off task in ECS (migrations run from backend/ folder in container)
docker run --rm \
  -e DATABASE_URL=<production-db-url> \
  <account-id>.dkr.ecr.<region>.amazonaws.com/tagmaster-api:latest \
  alembic upgrade head
```

---

## Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **Alembic Documentation**: https://alembic.sqlalchemy.org/
- **pytest Documentation**: https://docs.pytest.org/
- **Docker Documentation**: https://docs.docker.com/

---

## Support

For issues or questions:
- Open an issue on GitHub
- Contact the development team
- Check the API documentation at `/docs`

---

**Happy coding! 🥏**
