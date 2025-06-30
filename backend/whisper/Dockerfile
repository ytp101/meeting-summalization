# syntax=docker/dockerfile:1

# ─── Base Image ────────────────────────────────────────────────────────────────
FROM python:3.12-slim

# ─── Environment Settings ─────────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# ─── Install System Dependencies ─────────────────────────────────────────────────
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        git \
        libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# ─── Create Non-Root User & Working Directory ─────────────────────────────────────
RUN groupadd -g 1000 appgroup \
    && useradd -u 1000 -g appgroup -s /usr/sbin/nologin -m app
WORKDIR /usr/src/app

# ─── Install Python Dependencies ─────────────────────────────────────────────────
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ─── Copy Application Code ───────────────────────────────────────────────────────
COPY --chown=app:appgroup . .

# ─── Prepare Data Volume Directories ─────────────────────────────────────────────
# Mount /data as a Docker volume for input and transcript files
RUN mkdir -p /data/wav /data/transcript \
    && chown -R app:appgroup /data

# ─── Configure Hugging Face Caches ────────────────────────────────────────────────
ENV HF_HOME=/home/app/.cache
ENV TRANSFORMERS_CACHE=/home/app/.cache/huggingface
RUN mkdir -p $HF_HOME $TRANSFORMERS_CACHE \
    && chown -R app:appgroup $HF_HOME

# ─── Switch to Non-Root User ─────────────────────────────────────────────────────
USER app

# ─── Expose Service Port ─────────────────────────────────────────────────────────
EXPOSE 8003

# ─── Entrypoint ─────────────────────────────────────────────────────────────────
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]