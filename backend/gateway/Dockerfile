# setup 
FROM python:3.12.10-slim
WORKDIR /usr/local/app

# install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Create directory for uploaded files
RUN mkdir -p /usr/local/app/data/mp4/ && chmod 777 /usr/local/app/data/mp4/

# Expose port 8000
EXPOSE 8000

# setup app user 
RUN useradd app 
USER app

# run container 
COPY main.py ./
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 