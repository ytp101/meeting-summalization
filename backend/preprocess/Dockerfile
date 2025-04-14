# setup 
FROM python:3.12.10-slim
WORKDIR /usr/local/app

# install ffmpeg 
RUN apt-get -y update
RUN apt-get install -y ffmpeg

# install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for audio files and logs
RUN mkdir -p /usr/local/app/data/mp4/ && chmod 777 /usr/local/app/data/mp4/
RUN mkdir -p /usr/local/app/data/wav/ && chmod 777 /usr/local/app/data/wav/
RUN touch /usr/local/app/preprocess.log && chmod 666 /usr/local/app/preprocess.log

# Expose port 8001
EXPOSE 8001

# setup app user 
RUN useradd app 
USER app

# run container 
COPY main.py ./
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"] 