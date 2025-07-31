# syntax=docker/dockerfile:1.4

#########################################################
# Builder Stage: Install dependencies & compile requirements
#########################################################
FROM python:3.12-slim AS builder

# Avoid Python writing .pyc and buffer issues
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system build deps; retain ffmpeg (runtime) here for layer caching
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        pkg-config \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a separate prefix
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt

#########################################################
# Final Stage: Minimal runtime image
#########################################################
FROM python:3.12-slim AS runtime

# Configure environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin app \
    && mkdir -p /app /data/raw /data/converted \
    && chown -R app:appgroup /app /data

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
WORKDIR /app
COPY --chown=app:appgroup . /app

USER app

# Expose service port
EXPOSE 8001

# Optional: healthcheck for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl --fail http://localhost:8001/health || exit 1

# Entrypoint
ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
