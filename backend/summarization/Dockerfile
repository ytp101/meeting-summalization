# syntax=docker/dockerfile:1.4

#########################################################
# Builder Stage: Install build tools & Python dependencies
#########################################################
FROM python:3.12.10-slim AS builder

# Disable Python bytecode and buffer stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install build dependencies for Python packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install into isolated prefix
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt

#########################################################
# Runtime Stage: Minimal image with runtime dependencies
#########################################################
FROM python:3.12.10-slim AS runtime

# Metadata
LABEL org.opencontainers.image.description="Summarization Service: Converts transcripts into concise summaries"

# Configure environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create non-root user and data directories
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin app \
    && mkdir -p /app /data/transcript /data/summary \
    && chown -R app:appgroup /app /data

# Install runtime dependencies only
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
WORKDIR /app
COPY --chown=app:appgroup . /app/summarization
ENV PYTHONPATH=/app

# copy the bootstrapper and make it executable  
COPY docker-entrypoint.sh /usr/local/bin/  
RUN chmod +x /usr/local/bin/docker-entrypoint.sh  

# Switch to non-root user
USER app

# Expose service port
EXPOSE 8005

# Entrypoint: start Uvicorn
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh", "uvicorn", "summarization.main:app", "--host", "0.0.0.0", "--port", "8005"]