# Stage 1: Build dependencies
FROM python:3.11-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache gcc musl-dev postgresql-dev

# Copy requirements and install
COPY requirements.txt .
# Install dependencies system-wide in builder so runtime image can reuse /usr/local
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-alpine

WORKDIR /app

# Install runtime dependencies only
RUN apk add --no-cache postgresql-libs libffi

# Copy installed packages from builder
COPY --from=builder /usr/local /usr/local
ENV PATH=/usr/local/bin:$PATH

# Copy application code
COPY app /app/app
COPY alembic /app/alembic
COPY alembic.ini /app/

# Create non-root user
RUN adduser -D appuser && chown -R appuser:appuser /app /usr/local
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=5)" || exit 1

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
