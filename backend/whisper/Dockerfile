# Use CUDA base image for GPU support
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

# Set working directory
WORKDIR /usr/local/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Setup app user with proper home directory and data directories
RUN useradd app && \
    mkdir -p /home/app/.cache && \
    mkdir -p /usr/local/app/data/wav && \
    mkdir -p /usr/local/app/data/txt && \
    mkdir -p /usr/local/app/logs && \
    touch /usr/local/app/logs/whisper.log && \
    chmod 666 /usr/local/app/logs/whisper.log && \
    chown -R app:app /home/app && \
    chown -R app:app /usr/local/app

RUN mkdir -p /usr/local/app/data/txt && \
    chmod 777 /usr/local/app/data/txt

# Install Python dependencies
COPY requirements.txt ./
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 && \
    pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py ./
RUN chown -R app:app /usr/local/app

# Set environment variables
ENV HF_HOME=/home/app/.cache
ENV TRANSFORMERS_CACHE=/home/app/.cache/huggingface
ENV FORCE_CPU=0
ENV LOG_FILE=/usr/local/app/logs/whisper.log

# Switch to non-root user
USER app

# Expose port 8002
EXPOSE 8002

# Run container
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"] 