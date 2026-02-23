#!/bin/bash
set -e

echo "=== OpenClaw: Starting Setup on Jetson Orin Nano ==="

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./scripts/setup.sh)"
  exit 1
fi

# Ensure basic packages are present
echo "--> Installing dependencies..."
apt-get update && apt-get install -y ansible curl git

# Run Ansible Playbook
echo "--> Running Ansible configuration..."
# Need to ensure localhost works correctly
ansible-playbook ansible/setup_jetson.yml

echo "--> Building and Starting Docker Stack..."
# Assuming docker-compose is installed by ansible
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose not found, trying pip install..."
    pip3 install docker-compose
fi

# Bring up the stack
docker-compose -f docker/docker-compose.yml up -d --build

echo "=== Setup Complete! ==="
echo "Please check the logs with: docker-compose -f docker/docker-compose.yml logs -f"
