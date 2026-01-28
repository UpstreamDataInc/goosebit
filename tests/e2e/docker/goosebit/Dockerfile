# Multi-stage build for goosebit
FROM ghcr.io/astral-sh/uv:python3.14-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    postgresql-dev

# Set working directory
WORKDIR /app

# Enable bytecode compilation and disable dev dependencies
ENV UV_COMPILE_BYTECODE=1
ENV UV_NO_DEV=1
ENV UV_LINK_MODE=copy

# Copy dependency files and plugin source code for better caching
# For workspaces, we need the complete plugin directories before syncing
COPY pyproject.toml uv.lock ./
COPY plugins/ ./plugins/

# Install dependencies only (not the workspace members)
# Use --frozen instead of --locked since we don't have the main project files yet
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-workspace

# Copy the rest of the application
COPY . .

# Install the project and workspace members in non-editable mode
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

# Production stage
FROM python:3.14-alpine

# Install runtime dependencies
RUN apk add --no-cache \
    libpq \
    curl

# Create app user for security
RUN addgroup -g 1000 app && \
    adduser -D -u 1000 -G app app

# Create database directory
RUN mkdir -p /db && chown app:app /db

# Install gunicorn separately (not in project dependencies)
RUN pip install --no-cache-dir gunicorn

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder --chown=app:app /app/.venv /app/.venv

# Copy application code
COPY --chown=app:app . .

# Move configuration files
RUN mv /app/tests/e2e/docker/goosebit/aerich.toml /aerich.toml && \
    mv /app/tests/e2e/docker/goosebit/goosebit.yaml /app/goosebit.yaml

# Switch to non-root user
USER app

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose the application port
EXPOSE 60053

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# We currently do not fully support multiple workers. For more information, see:
# https://github.com/UpstreamDataInc/goosebit/issues/125
ENV GUNICORN_CMD_ARGS="--workers 1 --enable-stdio-inheritance"

# Default command: run database migrations and start the server
SHELL ["/bin/sh", "-c"]
CMD aerich upgrade && \
    gunicorn --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:60053 goosebit:app
