# syntax=docker/dockerfile:1

# ─── Base Image ────────────────────────────────────────────────────────────────
FROM python:3.12.10-slim

# ─── Environment Settings ─────────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# ─── Working Directory ───────────────────────────────────────────────────────────
WORKDIR /usr/src/app

# ─── System Dependencies ─────────────────────────────────────────────────────────
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# ─── Non-Root User Setup ─────────────────────────────────────────────────────────
RUN groupadd -g 1000 appgroup \
    && useradd -u 1000 -g appgroup -s /usr/sbin/nologin app

# ─── Python Dependencies ─────────────────────────────────────────────────────────
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ─── Copy Application Code ───────────────────────────────────────────────────────
COPY --chown=app:appgroup . .

# ─── Data Directories ────────────────────────────────────────────────────────────
# Ensure directories for raw and converted media exist under /data (Docker volume)
RUN mkdir -p /data/raw /data/converted \
    && chown -R app:appgroup /data

# ─── Switch to Non-Root User ─────────────────────────────────────────────────────
USER app

# ─── Expose Port & Entrypoint ────────────────────────────────────────────────────
EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
