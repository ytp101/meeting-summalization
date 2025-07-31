# syntax=docker/dockerfile:1.4

#########################################################
# Builder Stage: Install dependencies & build Python packages
#########################################################
FROM python:3.12-slim AS builder

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies needed to build and run diarization
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        pkg-config \
        libsndfile1 \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies to a dedicated prefix to optimize layer caching
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt

#########################################################
# Runtime Stage: Minimal image with non-root user
#########################################################
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create a non-root user and directories for data and cache
RUN groupadd -r appgroup && useradd -r -g appgroup -d /home/app -s /sbin/nologin app \
    && mkdir -p /data/wav /home/app/.cache \
    && chown -R app:appgroup /data /home/app/.cache

# Copy installed Python packages from builder stage
COPY --from=builder /install /usr/local

# Set working directory and copy application code
WORKDIR /home/app
COPY --chown=app:appgroup . /app/diarization
ENV PYTHONPATH=/app

COPY docker-entrypoint.sh /usr/local/bin/  
RUN chmod +x /usr/local/bin/docker-entrypoint.sh  

# Ensure pip-installed scripts in .local/bin are on PATH
ENV PATH="/home/app/.local/bin:$PATH"

# Switch to non-root user
USER app

# Expose service port for FastAPI
EXPOSE 8004

# Healthcheck for container orchestration
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl --fail http://localhost:8004/health || exit 1

# Entrypoint to start the Uvicorn server
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh", "uvicorn", "diarization.main:app", "--host", "0.0.0.0", "--port", "8004"]
