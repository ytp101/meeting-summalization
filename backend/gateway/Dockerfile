# use python 3.12.10-slim for small size image 
FROM python:3.12.10-slim

# update system
RUN apt-get -y update

# set work directory
WORKDIR /usr/local/app

# copy requirement file for gateway image 
COPY requirements.txt ./

# use pip to install libraries acccorind to requirement file
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8000 (prepare for frontend request (8000))
EXPOSE 8000

# Create the app user and add to the appgroup with fixed GID
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -s /bin/bash app

# Create directories with group write permissions
RUN mkdir -p /usr/local/app/data/mp4 /usr/local/app/data/txt && \
    chown -R app:appgroup /usr/local/app

# change to app user for run application
USER app

# copy application file & run application 
COPY main.py ./
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 