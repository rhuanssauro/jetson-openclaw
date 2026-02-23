# Base image optimized for Jetson Python
FROM python:3.10-slim-buster

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends 
    build-essential 
    libgpiod-dev 
    python3-pip 
    python3-dev 
    i2c-tools 
    git 
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Default command
CMD ["python3", "-u", "src/main.py"]
