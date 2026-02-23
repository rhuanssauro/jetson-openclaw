#!/bin/bash
set -e

echo "=== OpenClaw: Update & Restart ==="

echo "--> Pulling latest code..."
git pull origin main

echo "--> Rebuilding Docker stack..."
docker-compose -f docker/docker-compose.yml down
docker-compose -f docker/docker-compose.yml up -d --build

echo "=== Update Complete! ==="
