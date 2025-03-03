#!/bin/bash
set -e

# Script to build all base images from the unified Dockerfile
echo "Building Stock Prediction Platform base images..."

REGISTRY_PREFIX="stock-prediction-platform"

# Build all images from the multi-stage Dockerfile
echo "Building Python base image..."
docker build -t ${REGISTRY_PREFIX}/python:base --target python-base -f docker/base/Dockerfile .

echo "Building PyTorch base image..."
docker build -t ${REGISTRY_PREFIX}/pytorch:base --target pytorch-base -f docker/base/Dockerfile .

echo "Building Node.js base image..."
docker build -t ${REGISTRY_PREFIX}/node:base --target node-base -f docker/base/Dockerfile .

echo "Building combined base image (optional)..."
docker build -t ${REGISTRY_PREFIX}/combined:base --target combined-base -f docker/base/Dockerfile .

echo "All base images built successfully!"
echo "Available images:"
echo "- ${REGISTRY_PREFIX}/python:base"
echo "- ${REGISTRY_PREFIX}/pytorch:base"
echo "- ${REGISTRY_PREFIX}/node:base"
echo "- ${REGISTRY_PREFIX}/combined:base"