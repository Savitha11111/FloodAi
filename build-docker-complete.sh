#!/bin/bash

# FloodScope AI Complete Docker Build Script
echo "=========================================="
echo "FloodScope AI - Complete Docker Build"
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "Warning: docker-compose not found. Using docker compose instead."
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo "Building FloodScope AI Complete Docker Image..."
echo "This includes all APIs and functionality built-in."
echo ""

# Build the image
echo "Step 1: Building Docker image..."
docker build -t floodscope-ai:complete . --no-cache

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
else
    echo "❌ Docker build failed. Check the logs above."
    exit 1
fi

echo ""
echo "Step 2: Testing the image..."
# Test the image
docker run --rm -d --name floodscope-test -p 5001:5000 floodscope-ai:complete

# Wait a moment for startup
sleep 10

# Check if container is running
if docker ps | grep -q floodscope-test; then
    echo "✅ Container test successful!"
    docker stop floodscope-test
else
    echo "❌ Container test failed."
    exit 1
fi

echo ""
echo "=========================================="
echo "Build Complete! 🎉"
echo "=========================================="
echo ""
echo "To run the application:"
echo ""
echo "Option 1 - Quick Start (no API keys):"
echo "docker run -p 5000:5000 floodscope-ai:complete"
echo ""
echo "Option 2 - With API keys for full functionality:"
echo "docker run -p 5000:5000 \\"
echo "  -e OPENWEATHER_API_KEY=your_api_key \\"
echo "  -e GMAIL_USER=your_email@gmail.com \\"
echo "  -e GMAIL_APP_PASSWORD=your_app_password \\"
echo "  floodscope-ai:complete"
echo ""
echo "Option 3 - Using Docker Compose:"
echo "$COMPOSE_CMD -f docker-compose.complete.yml up"
echo ""
echo "Application will be available at: http://localhost:5000"
echo ""
echo "Features included:"
echo "- ✅ Flood risk analysis"
echo "- ✅ Interactive mapping"
echo "- ✅ AI chat assistant"
echo "- ✅ Email alerts"
echo "- ✅ Report generation"
echo "- ✅ Real-time monitoring"
echo ""