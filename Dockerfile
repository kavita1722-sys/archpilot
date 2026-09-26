# Multi-stage Dockerfile for ArchPilot Backend & Frontend

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy package definitions and install dependencies
COPY pyproject.toml README.md LICENSE ./
RUN pip install --upgrade pip && \
    pip install ".[dev]"

# Copy source code
COPY app/ ./app/
COPY ui/ ./ui/
COPY scripts/ ./scripts/
COPY docs/ ./docs/
COPY .env.example ./

# Install project package
RUN pip install -e .

EXPOSE 8000 8501

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
