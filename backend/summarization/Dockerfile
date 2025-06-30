# syntax=docker/dockerfile:1

# ─── Base Image ────────────────────────────────────────────────────────────────
FROM python:3.12.10-slim

# ─── Environment Settings ─────────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# ─── System Dependencies ─────────────────────────────────────────────────────────
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ─── Set Working Directory ───────────────────────────────────────────────────────
WORKDIR /usr/src/app

# ─── Non-Root User Setup ─────────────────────────────────────────────────────────
RUN groupadd -g 1000 appgroup \
    && useradd -u 1000 -g appgroup -s /usr/sbin/nologin app

# ─── Install Python Dependencies ─────────────────────────────────────────────────
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ─── Copy Application Code ───────────────────────────────────────────────────────
COPY --chown=app:appgroup . .

# ─── Prepare Data Volume Directories ─────────────────────────────────────────────
# Mount /data for transcript and summary files
RUN mkdir -p /data/transcript /data/summary \
    && chown -R app:appgroup /data

# ─── Switch to Non-Root User ─────────────────────────────────────────────────────
USER app

# ─── Expose Service Port ─────────────────────────────────────────────────────────
EXPOSE 8005

# ─── Entrypoint ─────────────────────────────────────────────────────────────────
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
