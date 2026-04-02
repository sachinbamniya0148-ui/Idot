FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    gcc g++ libffi-dev libssl-dev zlib1g-dev \
    libjpeg-dev libpng-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip --root-user-action=ignore && \
    pip install --no-cache-dir -r requirements.txt --root-user-action=ignore

COPY . .

RUN mkdir -p /data/uploads /data/downloads /data/logs /data/dictionaries \
    /tmp/zipcracker/uploads /tmp/zipcracker/downloads \
    /tmp/zipcracker/logs /tmp/zipcracker/dictionaries

ENV PORT=8080
ENV DATA_DIR=/data
ENV PYTHONUNBUFFERED=1
EXPOSE 8080

CMD ["python", "server.py"]
