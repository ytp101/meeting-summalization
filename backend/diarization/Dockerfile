# syntax=docker/dockerfile:1.4

#########################################################
# Builder Stage: Install dependencies & build Python packages
#########################################################
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        pkg-config \
        libsndfile1 \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt

#########################################################
# Runtime Stage: Slim image with matching UID/GID user
#########################################################
FROM python:3.12-slim AS runtime

# ARGs to set UID/GID for compatibility with host filesystem
ARG UID=1000
ARG GID=1000

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/app/.local/bin:$PATH" \
    PYTHONPATH=/app

ENV HF_HOME=/home/app/.cache/huggingface
ENV XDG_CACHE_HOME=/home/app/.cache

# Create user with specific UID:GID for volume permission compatibility
RUN groupadd -g 1000 appgroup && \
    useradd -m -u 1000 -g appgroup -s /sbin/nologin app && \
    mkdir -p /data/wav /home/app/.cache/huggingface && \
    chown -R 1000:1000 /data /home/app

RUN ln -s /home/app/.cache /.cache || true

# Copy Python packages from builder
COPY --from=builder /install /usr/local

# Working directory and application code
WORKDIR /home/app
COPY --chown=$UID:$GID . /app/diarization

# Entrypoint setup
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

USER app

EXPOSE 8004

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl --fail http://localhost:8004/health || exit 1

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh", "uvicorn", "diarization.main:app", "--host", "0.0.0.0", "--port", "8004"]
