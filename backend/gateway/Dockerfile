# use python 3.12.10-slim for small size image 
FROM python:3.12.10-slim

# set work directory
WORKDIR /usr/local/app

# copy requirement file for gateway image 
COPY requirements.txt ./

# use pip to install libraries acccorind to requirement file
RUN pip install --no-cache-dir -r requirements.txt

# create directory for uploaded files (which map to persistent volume) && give permession to write
RUN mkdir -p /usr/local/app/data/mp4/ && chmod 777 /usr/local/app/data/mp4/
RUN mkdir -p /usr/local/app/data/txt && chmod 777 /usr/local/app/data/txt

# Expose port 8000 (prepare for frontend request (8000))
EXPOSE 8000

# setup app user 
RUN useradd app 
USER app

# run container 
COPY main.py ./
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 