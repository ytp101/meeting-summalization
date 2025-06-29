# Use official slim Python base
FROM python:3.12.10-slim

# --------------------
# 1. Environment
# --------------------
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /usr/local/app

# --------------------
# 2. System deps
# --------------------
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# --------------------
# 3. Python deps
# --------------------
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# --------------------
# 4. App user & dirs
# --------------------
RUN groupadd -g 1000 appgroup \
    && useradd -u 1000 -g appgroup -s /usr/sbin/nologin app \
    && mkdir -p data/mp4 data/wav \
    && chown -R app:appgroup /usr/local/app

USER app

# --------------------
# 5. Copy application
# --------------------
COPY --chown=app:appgroup . .

# --------------------
# 6. Expose & run
# --------------------
EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
