# syntax=docker/dockerfile:1

FROM python:3.12.10-slim

# ─── System Dependencies ─────────────────────────────────────────────────────────
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# ─── Set Working Directory ───────────────────────────────────────────────────────
WORKDIR /usr/src/app

# ─── Non-Root User Setup ─────────────────────────────────────────────────────────
RUN groupadd -g 1000 appgroup \
    && useradd -u 1000 -g appgroup -s /bin/bash app

# ─── Install Python Dependencies ─────────────────────────────────────────────────
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ─── Copy Application Code ───────────────────────────────────────────────────────
COPY --chown=app:appgroup . .

# ─── Prepare Persistent Data Directories ─────────────────────────────────────────
RUN mkdir -p /data/raw /data/converted /data/transcript /data/summary \
    && chown -R app:appgroup /data

# ─── Switch to Non-Root User ─────────────────────────────────────────────────────
USER app

# ─── Port & Entrypoint ───────────────────────────────────────────────────────────
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
