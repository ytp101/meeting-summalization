# ---- Base image ----
FROM python:3.11-slim

# ---- Working directory ----
WORKDIR /app

# ---- Install dependencies ----
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy your app ----
COPY . .

# ---- Expose FastAPI ----
EXPOSE 8000

# ---- Start FastAPI ----
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010"]
