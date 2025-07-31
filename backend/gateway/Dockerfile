# syntax=docker/dockerfile:1.4

#########################################################
# Builder Stage: Install build tools & Python dependencies
#########################################################
FROM python:3.12-slim AS builder

# Disable bytecode and buffer
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /install

# Install system packages needed for builds and psycopg2 (DB driver)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a separate prefix for layer caching
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt

#########################################################
# Runtime Stage: Minimal image with non-root user
#########################################################
FROM python:3.12-slim AS runtime

# Runtime environment settings
env PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create non-root user and data directories
RUN groupadd -r appgroup && useradd -r -g appgroup -d /usr/src/app -s /sbin/nologin app \
    && mkdir -p /usr/src/app /data/raw /data/converted /data/transcript /data/summary \
    && chown -R app:appgroup /usr/src/app /data

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Set working directory and copy application code
WORKDIR /usr/src/app
COPY --chown=app:appgroup . /app/gateway
ENV PYTHONPATH=/app

# copy the bootstrapper and make it executable  
COPY docker-entrypoint.sh /usr/local/bin/  
RUN chmod +x /usr/local/bin/docker-entrypoint.sh 

# Switch to non-root user
USER app

# Expose HTTP port
EXPOSE 8000

# Healthcheck for orchestration
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl --fail http://localhost:8000/healthcheck || exit 1

# Entrypoint to launch FastAPI via Uvicorn
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh", "uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
