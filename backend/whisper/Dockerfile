# Use CUDA base image for GPU support
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

# Set working directory
WORKDIR /usr/local/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    python3.10-venv \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
ENV VIRTUAL_ENV=/usr/local/app/venv
RUN python3.10 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Setup app user with proper home directory and data directories
RUN useradd app && \
    mkdir -p /home/app/.cache && \
    mkdir -p /usr/local/app/data/wav && \
    mkdir -p /usr/local/app/data/txt && \
    touch /usr/local/app/whisper.log && \
    chown -R app:app /home/app && \
    chown -R app:app /usr/local/app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py ./
RUN chown -R app:app /usr/local/app

# Set environment variables
ENV HF_HOME=/home/app/.cache
ENV TRANSFORMERS_CACHE=/home/app/.cache/huggingface

# Switch to non-root user
USER app

# Expose port 8002
EXPOSE 8002

# Run container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"] 