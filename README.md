# Disc Golf Tag League API

A FastAPI-based backend for managing disc golf tag leagues with dynamic rankings, score tracking, and role-based access control.

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# From repository root
# `docker compose` will load variables from the project-level `.env` file
# (located at the repository root) for variable substitution. Edit that file
# to configure the Postgres instance used by Compose (for example:
# `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`). The application also
# uses `backend/.env` (copy from `backend/.env.example`) for runtime settings.
docker compose up -d
```

API will be available at: http://localhost:8000

### Local Development

```bash
# From repository root
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

## ⚠️ Important: Working Directory

**Most backend commands must be run from the `backend/` folder:**

```bash
# ❌ WRONG - From repository root
alembic upgrade head  # This will fail!

# ✅ CORRECT - From backend folder
cd backend
alembic upgrade head  # This works!
```

### Commands that need `backend/` folder:
- `alembic` (all database migration commands)
- `pytest` (running tests)
- `uvicorn` (starting the API server)
- `python -m app.main` (running Python scripts)

### Commands that work from root:
- `docker-compose` (Docker commands)
- `git` (version control)

## 📁 Project Structure

```
TagMaster/                    # Repository root
├── backend/                  # Backend API (FastAPI) - RUN COMMANDS FROM HERE
│   ├── app/                 # Application code
│   ├── tests/               # Test suite
│   ├── alembic/             # Database migrations
│   ├── requirements.txt     # Python dependencies
│   ├── alembic.ini          # Alembic configuration
│   ├── pytest.ini           # Pytest configuration
│   └── .env                 # Environment variables (create from .env.example)
├── docker-compose.yml       # Local development setup
└── specs/                   # Feature documentation
```

## 🗄️ Database Migrations

**All Alembic commands must be run from the `backend/` folder!**

```bash
cd backend  # ← IMPORTANT: Switch to backend folder first!

# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# View current version
alembic current
```

## 🧪 Testing

**All pytest commands must be run from the `backend/` folder!**

```bash
cd backend  # ← IMPORTANT: Switch to backend folder first!

# Run all tests
pytest

# Run specific test types
pytest -m unit
pytest -m integration
pytest -m contract

# Run with coverage
pytest --cov=app --cov-report=html
```

## 📚 API Documentation

Once the API is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Development Workflow

1. **Start development environment:**
   ```bash
   # From repository root
   docker-compose up -d
   ```

2. **Make code changes** in `backend/app/`

3. **Create database migration** (if models changed):
   ```bash
   cd backend
   alembic revision --autogenerate -m "your change description"
   ```

4. **Apply migration:**
   ```bash
   cd backend
   alembic upgrade head
   ```

5. **Run tests:**
   ```bash
   cd backend
   pytest
   ```

6. **Commit changes:**
   ```bash
   # From repository root
   git add .
   git commit -m "your commit message"
   ```

## 🐛 Troubleshooting

### "alembic: command not found"
**Solution**: You're in the wrong directory or dependencies aren't installed
```bash
cd backend
pip install -r requirements.txt
```

### "Can't locate revision" or "No module named 'app'"
**Solution**: Make sure you're in the `backend/` folder
```bash
cd backend  # Then run your command
```

### Database connection error
**Solution**: Make sure PostgreSQL is running
```bash
# Check if containers are running
docker-compose ps

# View logs
docker-compose logs db
```

## 📖 For More Details

See the complete documentation in:
- [`specs/001-tag-league-api/quickstart.md`](specs/001-tag-league-api/quickstart.md) - Detailed setup guide
- [`specs/001-tag-league-api/plan.md`](specs/001-tag-league-api/plan.md) - Implementation plan
- [`specs/001-tag-league-api/spec.md`](specs/001-tag-league-api/spec.md) - Feature specification

## 📝 License

[Your License Here]
