# Use NVIDIA’s CUDA runtime base image for GPU support
FROM nvidia/cuda:12.8.1-cudnn-runtime-ubuntu22.04

# Set a non-root user and working directory
RUN groupadd -g 1000 appgroup \
 && useradd -m -u 1000 -g appgroup -s /bin/bash app
WORKDIR /usr/local/app

# Install system dependencies in one layer and clean up
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-pip \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Create application directories and set ownership
RUN mkdir -p data/wav data/txt \
 && chown -R app:appgroup .

# Prepare Hugging Face cache dirs
USER app
ENV HF_HOME=/home/app/.cache
ENV TRANSFORMERS_CACHE=/home/app/.cache/huggingface
RUN mkdir -p $HF_HOME $TRANSFORMERS_CACHE

# Expose the service port
EXPOSE 8002

# Copy the application code
COPY --chown=app:appgroup main.py ./

# Run Uvicorn under the non-root user
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003", "--log-level", "info"]
