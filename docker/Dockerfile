# Dockerfile — Development / CI image for x86_64
# Uses standard python:3.10-slim for local dev and CI pipelines.
# For Jetson Orin Nano (ARM64 + CUDA), use Dockerfile.jetson instead.
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

# Run as non-root user; GPIO/I2C access is granted via group membership in docker-compose
RUN groupadd -r openclaw && useradd -r -g openclaw -s /sbin/nologin appuser
USER appuser

# Default command
CMD ["python3", "-u", "src/main.py"]
