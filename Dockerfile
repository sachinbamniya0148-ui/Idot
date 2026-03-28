FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    gcc g++ libffi-dev libssl-dev zlib1g-dev \
    libjpeg-dev libpng-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /tmp/zipcracker/uploads /tmp/zipcracker/downloads \
    /tmp/zipcracker/logs /tmp/zipcracker/dictionaries

EXPOSE 8080
CMD ["python", "start.py"]
