# syntax=docker/dockerfile:1.4

#########################################################
# Builder Stage: Install build tools & Python dependencies
#########################################################
FROM python:3.12.10-slim AS builder

# Disable Python bytecode and buffering
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install build dependencies for Whisper and audio processing
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        pkg-config \
        ffmpeg \
        libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into an isolated prefix
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt

#########################################################
# Runtime Stage: Minimal image with runtime dependencies
#########################################################
FROM python:3.12.10-slim AS runtime

# Metadata
LABEL org.opencontainers.image.description="Whisper ASR Service: Speech-to-text with OpenAI Whisper"

# Configure Python environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create non-root user and directories for data/cache
RUN groupadd -r appgroup && useradd -r -g appgroup -d /usr/src/app -s /sbin/nologin app \
    && mkdir -p /usr/src/app /data/wav /data/transcript /home/app/.cache/huggingface \
    && chown -R app:appgroup /usr/src/app /data /home/app/.cache

# Install only runtime system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code into place
WORKDIR /usr/src/app
COPY --chown=app:appgroup . /app/whisper 
ENV PYTHONPATH=/app

# copy the bootstrapper and make it executable  
COPY docker-entrypoint.sh /usr/local/bin/  
RUN chmod +x /usr/local/bin/docker-entrypoint.sh  

# Configure Hugging Face cache paths
ENV HF_HOME=/home/app/.cache
ENV TRANSFORMERS_CACHE=/home/app/.cache/huggingface

# Ensure user-local scripts are on PATH
ENV PATH="/home/app/.local/bin:$PATH"

# Switch to non-root user
USER app

# Expose service port
EXPOSE 8003

# Healthcheck for orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl --fail http://localhost:8003/healthcheck || exit 1

# Entrypoint: launch Uvicorn server
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh", "uvicorn", "whisper.main:app", "--host", "0.0.0.0", "--port", "8003"]
