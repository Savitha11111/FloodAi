#!/bin/bash
# FloodScope AI - Mac/Linux Installation Script

echo "🌊 FloodScope AI - Local Installation Script"
echo "============================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements-local.txt

# Create .streamlit directory
echo "⚙️  Setting up Streamlit configuration..."
mkdir -p .streamlit

# Create Streamlit config
cat > .streamlit/config.toml << EOF
[server]
headless = true
address = "0.0.0.0"
port = 5000

[browser]
gatherUsageStats = false
EOF

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "🔑 Creating environment file..."
    cat > .env << EOF
# FloodScope AI - Enhanced Environment Configuration
# Real-time Weather Data API
OPENWEATHER_API_KEY=your_openweather_api_key_here

# Real-time Flood Monitoring API
AMBEE_API_KEY=your_ambee_api_key_here

# Satellite Imagery APIs
SENTINELHUB_CLIENT_ID=your_sentinelhub_client_id_here
SENTINELHUB_CLIENT_SECRET=your_sentinelhub_client_secret_here
EOF
    echo "⚠️  Please edit .env file and add your API keys before running the application"
    echo ""
    echo "📖 API Key Sources:"
    echo "  - OpenWeather: https://openweathermap.org/api"
    echo "  - Ambee: https://www.getambee.com/"
    echo "  - Sentinel Hub: https://apps.sentinel-hub.com/"
else
    echo "✅ Environment file already exists"
fi

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run: source venv/bin/activate"
echo "3. Run: streamlit run app.py --server.port 5000"
echo ""
echo "The application will be available at: http://localhost:5000"