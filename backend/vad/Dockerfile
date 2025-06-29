# Use a slim Python base image
FROM python:3.12-slim

# Install system dependencies (ffmpeg for audio I/O, git for HF models, and cleanup)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ffmpeg \
       git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /usr/local/app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the port the service will run on
EXPOSE 8003

# Ensure HF_TOKEN is provided at runtime
ENV HF_TOKEN=""

# Run the FastAPI app with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
