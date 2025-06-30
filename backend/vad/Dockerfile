# syntax=docker/dockerfile:1

# ─── Base Image ────────────────────────────────────────────────────────────────
# Use a slim Python image for minimal footprint
FROM python:3.12-slim

# ─── Environment Configuration ───────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# ─── System Dependencies ─────────────────────────────────────────────────────────
# Install ffmpeg for audio I/O, git for model downloads, libsndfile for audio
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        git \
        libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# ─── Create Non-Root User & Group ────────────────────────────────────────────────
RUN groupadd -g 1000 appgroup \
    && useradd -m -u 1000 -g appgroup -s /usr/sbin/nologin app

# ─── Prepare Data & Cache Directories (root) ──────────────────────────────────────
# Create /data for WAV inputs and Hugging Face cache dirs
RUN mkdir -p /data/wav /home/app/.cache/huggingface \
    && chown -R app:appgroup /data /home/app/.cache

# ─── Switch to Non-Root User & Set Working Directory ─────────────────────────────
USER app
WORKDIR /home/app/workdir

# Ensure user-local scripts are on PATH
ENV PATH="/home/app/.local/bin:$PATH"

# ─── Install Python Dependencies ─────────────────────────────────────────────────
COPY --chown=app:appgroup requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ─── Copy Application Code ───────────────────────────────────────────────────────
COPY --chown=app:appgroup . .

# ─── Expose Service Port ─────────────────────────────────────────────────────────
EXPOSE 8002

# ─── Entrypoint ─────────────────────────────────────────────────────────────────
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
