# Multi-stage build for goosebit
FROM python:3.13-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    postgresql-dev \
    curl

# Install Poetry
RUN pip install --no-cache-dir poetry

# Set working directory
WORKDIR /app

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Configure poetry: no dev dependencies, no virtual env (using container)
RUN poetry config virtualenvs.create false && poetry install --only=main --no-root

# Copy application code
COPY . .

# Install the application
RUN poetry install --only=main

# Production stage
FROM python:3.13-alpine

RUN apk add --no-cache curl

# Install runtime dependencies
RUN pip install --no-cache-dir gunicorn

# Create database directory
RUN mkdir -p db/

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Create docker-specific aerich config
RUN printf '[tool.aerich]\ntortoise_orm = "goosebit.db.config.TORTOISE_CONF"\nlocation = "/app/goosebit/db/migrations"\n' > /aerich.toml

RUN mv /app/e2e/goosebit.yaml /app/goosebit.yaml

# Expose the application port
EXPOSE 60053

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# We currently do not fully support multiple workers. For more information, see:
# https://github.com/UpstreamDataInc/goosebit/issues/125
ENV GUNICORN_CMD_ARGS="--workers 1 --enable-stdio-inheritance"

# Default command: run database migrations and start the server
CMD ["sh", "-c", "poetry run aerich upgrade && gunicorn --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:60053 goosebit:app"]
