# Use CUDA base image for GPU support 
FROM nvidia/cuda:12.8.1-cudnn-runtime-ubuntu22.04

# Set work directory
WORKDIR /usr/local/app

# Install system dependencies
RUN apt-get -y update 

# make wav and txt directory 
RUN mkdir -p /usr/local/app/data/wav && chmod 777 /usr/local/app/data/wav
RUN mkdir -p /usr/local/app/data/txt && chmod 777 /usr/local/app/data/txt

# install pip 
RUN apt-get install python-pip -y

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# make directory for cache 
RUN mkdir -p /home/app/.cache

# Set environment variables for logging and cache
ENV HF_HOME=/home/app/.cache
ENV TRANSFORMERS_CACHE=/home/app/.cache/huggingface

# useradd app user and switch to 
RUN useradd app 
USER app

# Expose port 8002
EXPOSE 8002

# Copy application code
COPY main.py ./

# Run container
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"] 