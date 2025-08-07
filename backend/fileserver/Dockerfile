# syntax=docker/dockerfile:1.4

#########################################################
# Builder Stage: Install dependencies & compile Python packages
#########################################################
FROM python:3.12-slim AS builder

# Disable bytecode generation and buffering
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /install

# Install dependencies into a separate prefix for layer caching
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt

#########################################################
# Runtime Stage: Minimal image with non-root user
#########################################################
FROM python:3.12-slim AS runtime

# Environment settings
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create non-root user and application directory
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin app \
    && mkdir -p /app \
    && chown -R app:appgroup /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Set working directory and copy application code
WORKDIR /app
COPY --chown=app:appgroup . /app/file_server
ENV PYTHONPATH=/app

# copy the bootstrapper and make it executable  
COPY docker-entrypoint.sh /usr/local/bin/  
RUN chmod +x /usr/local/bin/docker-entrypoint.sh  

# Switch to non-root user
USER app

# Expose service port (matches FastAPI run port)
EXPOSE 8010

# Healthcheck endpoint (assumes GET / responds with 200)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8010/ || exit 1

# Entrypoint: start FastAPI via Uvicorn
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh", "uvicorn", "file_server.main:app", "--host", "0.0.0.0", "--port", "8010"]
