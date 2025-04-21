# Use CUDA base image for GPU support 
FROM nvidia/cuda:12.8.1-cudnn-runtime-ubuntu22.04

# Set work directory
WORKDIR /usr/local/app

# Install system dependencies
RUN apt-get -y update && apt-get install -y python3-pip && apt-get install -y ffmpeg

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8002
EXPOSE 8002

# Create the app user and add to the appgroup with fixed GID
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -s /bin/bash app

# Create directories with group write permissions
RUN mkdir -p /usr/local/app/data/wav /usr/local/app/data/txt && \
    chown -R app:appgroup /usr/local/app

# make directory for cache 
RUN mkdir -p /home/app/.cache && \
    chown -R app:appgroup /home/app/.cache

# Set environment variables for logging and cache
ENV HF_HOME=/home/app/.cache
ENV TRANSFORMERS_CACHE=/home/app/.cache/huggingface

# change to app user for running application
USER app

# Copy application code run application 
COPY main.py ./
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"] 