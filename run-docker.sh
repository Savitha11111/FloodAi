#!/bin/bash

echo "🌊 FloodScope AI - Single Command Docker Deployment"
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file with default values..."
    cat > .env << EOF
# FloodScope AI - Environment Configuration
OPENWEATHER_API_KEY=your_openweather_api_key_here
AMBEE_API_KEY=your_ambee_api_key_here
SENTINELHUB_CLIENT_ID=your_sentinelhub_client_id_here
SENTINELHUB_CLIENT_SECRET=your_sentinelhub_client_secret_here
EOF
    echo "⚠️  Edit .env file with your API keys for full functionality"
fi

# Stop any existing container
echo "🛑 Stopping any existing FloodScope containers..."
docker-compose down 2>/dev/null || true

# Build and run
echo "🔨 Building FloodScope AI Docker image..."
docker-compose build

if [ $? -eq 0 ]; then
    echo "🚀 Starting FloodScope AI..."
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ FloodScope AI is now running!"
        echo "🌐 Access your application at: http://localhost:5000"
        echo ""
        echo "📊 Commands:"
        echo "  View logs: docker-compose logs -f"
        echo "  Stop app:  docker-compose down"
        echo "  Restart:   docker-compose restart"
        echo ""
        echo "⏳ Please wait 30-60 seconds for the application to fully load..."
    else
        echo "❌ Failed to start FloodScope AI"
        exit 1
    fi
else
    echo "❌ Failed to build FloodScope AI"
    exit 1
fi