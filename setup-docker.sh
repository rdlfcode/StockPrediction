#!/bin/bash
set -e

# Stock Prediction Platform Docker Setup Script

echo "==================================================="
echo "Stock Prediction Platform Docker Setup"
echo "==================================================="

# Make scripts executable
chmod +x docker/base/build-base-images.sh

# Build base images
echo "Building base Docker images..."
./docker/base/build-base-images.sh

# Build and start the services
echo -e "\nBuilding and starting services..."
docker-compose -f docker/docker-compose.yml build
docker-compose -f docker/docker-compose.yml up -d

echo -e "\n==================================================="
echo "Setup complete! Services are available at:"
echo "- Dashboard: http://localhost:8000"
echo "- Data Ingestion API: http://localhost:8001"
echo "- Model Service API: http://localhost:8002"
echo "- MinIO Console: http://localhost:9001"
echo "==================================================="