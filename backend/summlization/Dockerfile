# Use Python slim image for smaller size
FROM python:3.12.10-slim

# Set working directory
WORKDIR /usr/local/app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Setup app user and directories
RUN useradd app && \
    mkdir -p /usr/local/app/data/txt && \
    touch /usr/local/app/summarization.log && \
    chown -R app:app /usr/local/app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py ./
RUN chown -R app:app /usr/local/app

# Set environment variables
ENV BASE_DIR_TXT=/usr/local/app/data/txt/ \
    MODEL_ID=llama3 \
    OLLAMA_HOST=http://ollama:11434 \
    MAX_TOKENS=4096 \
    TEMPERATURE=0.2 \
    REQUEST_TIMEOUT=300 \
    PORT=8003

# Switch to non-root user
USER app

# Expose port 8003
EXPOSE 8003

# Run container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
