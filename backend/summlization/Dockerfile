# Use Python slim image for small container size 
FROM python:3.12.10-slim

# Set working directory
WORKDIR /usr/local/app

# Install system dependencies
RUN apt-get -y update

# setup txt directory 
RUN mkdir -p /usr/local/app/data/txt && chmod 777 /usr/local/app/data/txt

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV BASE_DIR_TXT=/usr/local/app/data/txt/ \
    MODEL_ID=llama3 \
    OLLAMA_HOST=http://ollama:11434 \
    MAX_TOKENS=4096 \
    TEMPERATURE=0.2 \
    REQUEST_TIMEOUT=300 \
    PORT=8003 

# Expose port 8003
EXPOSE 8003

# Copy application code
COPY main.py ./

# Switch to non-root user
RUN useradd app
USER app

# Run container
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
