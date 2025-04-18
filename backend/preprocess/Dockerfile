# use python:3.12.10-slim for decrease image size 
FROM python:3.12.10-slim

# set work directory
WORKDIR /usr/local/app

# update system and install ffmpeg (nesscessary for mp4 or mp3 to wav) 
RUN apt-get -y update
RUN apt-get install -y ffmpeg

# copy requirements file and install dependencies according to requirements file 
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8001 prepare for gateway to preprocess request (8001)
EXPOSE 8001

# Create the app user and add to the appgroup with fixed GID
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -s /bin/bash app

# Create directories with group write permissions
RUN mkdir -p /usr/local/app/data/mp4 /usr/local/app/data/txt /usr/local/app/data/audio /usr/local/app/data/wav && \
    chown -R app:appgroup /usr/local/app

# change to app user for running application
USER app

# copy application file & run application 
COPY main.py ./
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"] 