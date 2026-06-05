#!/bin/bash

echo "Starting services sequentially to prevent WSL crash..."

# 1. Start database first
echo "Starting PostgreSQL..."
docker-compose up -d postgres

# Wait for healthy
echo "Waiting for PostgreSQL to be healthy..."
sleep 10

# 2. Start API (heavy ML models load here)
echo "Starting API (transcription service)..."
docker-compose up -d api

# Wait for models to load
echo "Waiting 60s for ML models to load..."
sleep 60

# 3. Start analysis (another heavy ML service)
echo "Starting Analysis service..."
docker-compose up -d analysis

# Wait for models to load
echo "Waiting 60s for analysis models to load..."
sleep 60

# 4. Start dashboard (lightweight)
echo "Starting Dashboard..."
docker-compose up -d dashboard

echo "All services started!"
echo "Check status with: docker-compose ps"
echo "View logs with: docker-compose logs -f"