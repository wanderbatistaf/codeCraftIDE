#!/bin/bash

# Docker Deploy Script for CodeCraftIDE-4gl
# This script builds, tags, and pushes images to Docker registry

# Configuration
REGISTRY_USER="${DOCKER_REGISTRY_USER:-your-dockerhub-username}"
IMAGE_PREFIX="${REGISTRY_USER}/codecraftide-4gl"
VERSION="${1:-latest}"

echo "=========================================="
echo "CodeCraftIDE-4gl Docker Deploy Script"
echo "=========================================="
echo "Registry: ${REGISTRY_USER}"
echo "Version: ${VERSION}"
echo ""

# Check if logged in to Docker
echo "Checking Docker login status..."
if ! docker info | grep -q "Username"; then
    echo "ERROR: Not logged in to Docker. Please run 'docker login' first."
    exit 1
fi

echo "✓ Docker login verified"
echo ""

# Build and tag backend image
echo "Building backend image..."
docker build -t ${IMAGE_PREFIX}-backend:${VERSION} -f Dockerfile .
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to build backend image"
    exit 1
fi
echo "✓ Backend image built"

# Also tag as latest if version is specified
if [ "${VERSION}" != "latest" ]; then
    docker tag ${IMAGE_PREFIX}-backend:${VERSION} ${IMAGE_PREFIX}-backend:latest
fi

# Build and tag studio image
echo ""
echo "Building studio image..."
docker build -t ${IMAGE_PREFIX}-studio:${VERSION} -f studio/Dockerfile ./studio
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to build studio image"
    exit 1
fi
echo "✓ Studio image built"

# Also tag as latest if version is specified
if [ "${VERSION}" != "latest" ]; then
    docker tag ${IMAGE_PREFIX}-studio:${VERSION} ${IMAGE_PREFIX}-studio:latest
fi

# Push images to registry
echo ""
echo "Pushing images to Docker registry..."
echo ""

echo "Pushing backend image (${VERSION})..."
docker push ${IMAGE_PREFIX}-backend:${VERSION}
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to push backend image"
    exit 1
fi

if [ "${VERSION}" != "latest" ]; then
    echo "Pushing backend image (latest)..."
    docker push ${IMAGE_PREFIX}-backend:latest
fi

echo ""
echo "Pushing studio image (${VERSION})..."
docker push ${IMAGE_PREFIX}-studio:${VERSION}
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to push studio image"
    exit 1
fi

if [ "${VERSION}" != "latest" ]; then
    echo "Pushing studio image (latest)..."
    docker push ${IMAGE_PREFIX}-studio:latest
fi

echo ""
echo "=========================================="
echo "✓ All images pushed successfully!"
echo "=========================================="
echo ""
echo "Images pushed:"
echo "  - ${IMAGE_PREFIX}-backend:${VERSION}"
echo "  - ${IMAGE_PREFIX}-studio:${VERSION}"
if [ "${VERSION}" != "latest" ]; then
    echo "  - ${IMAGE_PREFIX}-backend:latest"
    echo "  - ${IMAGE_PREFIX}-studio:latest"
fi
echo ""
echo "To deploy on another server:"
echo "  1. Copy docker-compose.production.yml to the server"
echo "  2. Set DOCKER_REGISTRY_USER environment variable"
echo "  3. Run: docker-compose -f docker-compose.production.yml pull"
echo "  4. Run: docker-compose -f docker-compose.production.yml up -d"
echo ""
