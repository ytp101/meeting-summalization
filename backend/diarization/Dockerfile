# syntax=docker/dockerfile:1

# ─── Base Image ────────────────────────────────────────────────────────────────
# Use slim Python for size; GPU support via nvidia runtime
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

# ─── Create Non-Root User ─────────────────────────────────────────────────────────
RUN groupadd -g 1000 appgroup \
    && useradd -u 1000 -g appgroup -s /usr/sbin/nologin -m app

# ─── Prepare Data & Cache Directories (as root) ───────────────────────────────────
RUN mkdir -p /data/wav /home/app/.cache/huggingface \
    && chown -R app:appgroup /data /home/app/.cache

# ─── Switch to Non-Root User & Set Working Directory ─────────────────────────────
USER app
WORKDIR /home/app/workdir

# ─── Ensure User Local Bin is on PATH for pip-installed scripts ──────────────────
ENV PATH="/home/app/.local/bin:$PATH"

# ─── Copy and Install Python Dependencies ─────────────────────────────────────────
COPY --chown=app:appgroup requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ─── Copy Application Code ───────────────────────────────────────────────────────
COPY --chown=app:appgroup . .

# ─── Expose Service Port ─────────────────────────────────────────────────────────
EXPOSE 8004

# ─── Entrypoint ─────────────────────────────────────────────────────────────────
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
