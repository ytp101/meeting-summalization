# syntax=docker/dockerfile:1.4

FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /install

COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt

# -----------------------------

FROM python:3.12-slim AS runtime

ARG UID=1000
ARG GID=1000

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

RUN groupadd -g ${GID} appgroup && \
    useradd -m -u ${UID} -g appgroup -s /sbin/nologin app && \
    mkdir -p /app && chown -R app:appgroup /app

WORKDIR /app
COPY --from=builder /install /usr/local

# Copy the renamed folder into /app
COPY --chown=app:appgroup . /app

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

USER app

EXPOSE 8010

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl --fail http://localhost:8010/healthcheck || exit 1

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]
