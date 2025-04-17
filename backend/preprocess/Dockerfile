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

# Create directories for audio files
RUN mkdir -p /usr/local/app/data/mp4/ && chmod 777 /usr/local/app/data/mp4/
RUN mkdir -p /usr/local/app/data/wav/ && chmod 777 /usr/local/app/data/wav/

# Expose port 8001 prepare for gateway to preprocess request (8001)
EXPOSE 8001

# setup app user to run application
RUN useradd app 
USER app

# copy application file & run container 
COPY main.py ./
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"] 