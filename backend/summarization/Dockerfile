# Use a minimal Python image for small footprint
FROM python:3.12.10-slim

# Ensure stdout/stderr are unbuffered (easier logging)
ENV PYTHONUNBUFFERED=1

# Install any OS-level dependencies (none special for gateway)
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /usr/local/app

# Copy & install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app will run on
EXPOSE 8004

# Create a non-root user & group
RUN groupadd -g 1000 appgroup \
 && useradd -u 1000 -g appgroup -s /usr/sbin/nologin app \
 # Create application data dirs and give ownership to `app`
 && mkdir -p data/mp4 data/txt \
 && chown -R app:appgroup /usr/local/app

# Switch to the unprivileged user
USER app

# Copy application code in
COPY main.py ./

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
