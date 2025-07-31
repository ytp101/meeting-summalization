# syntax=docker/dockerfile:1.4

#########################################################
# Builder Stage: Install build tools & Python dependencies
#########################################################
FROM python:3.12.10-slim AS builder

# Disable Python bytecode & buffer stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies needed for VAD and model handling
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        ffmpeg \
        libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies into isolated prefix
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt

#########################################################
# Runtime Stage: Minimal image with runtime dependencies
#########################################################
FROM python:3.12.10-slim AS runtime

# Metadata
LABEL org.opencontainers.image.description="Voice Activity Detection (VAD) Service"

# Configure environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create non-root user & data/cache directories
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin app \
    && mkdir -p /app /data/wav /home/app/.cache/huggingface \
    && chown -R app:appgroup /app /data /home/app/.cache

# Install only runtime system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /install /usr/local

# Set working directory and copy application code
WORKDIR /app
COPY --chown=app:appgroup . /app/vad
ENV PYTHONPATH=/app


# Ensure user-local scripts are on PATH
ENV PATH="/home/app/.local/bin:$PATH"

# Switch to non-root user
USER app

# Expose service port
EXPOSE 8002

# Healthcheck endpoint (assumes GET /health returns 200)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl --fail http://localhost:8002/health || exit 1

# Entrypoint: start Uvicorn
ENTRYPOINT ["uvicorn", "vad.main:app", "--host", "0.0.0.0", "--port", "8002"]
