# Use NVIDIA base image for CUDA support
FROM nvidia/cuda:12.8.1-cudnn-runtime-ubuntu22.04

# Install system dependencies:
#  - python3 & python3-pip
#  - ffmpeg / audio libs
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      python3 python3-pip \
      ffmpeg libsndfile1 \
 && rm -rf /var/lib/apt/lists/*

# Set working dir
WORKDIR /usr/local/app

# Copy and install Python deps as root
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# Now create unprivileged user & own the app dirs
RUN groupadd -g 1000 appgroup \
 && useradd -u 1000 -g appgroup -s /bin/bash app \
 && mkdir -p /usr/local/app/data/wav /home/app/.cache /home/app/.config/matplotlib \
 && chown -R app:appgroup /usr/local/app /home/app

# Switch to app user
USER app

# Copy your code
COPY main.py ./

# Expose your port
EXPOSE 8004

# Run via the uvicorn that was installed into /usr/local/bin
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
