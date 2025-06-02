# FloodScope - An AI-Driven Flood Mapping System Using Dual Satellite Imagery

An advanced AI-powered flood detection and monitoring system that provides comprehensive, real-time flood risk assessments using cutting-edge technologies and multi-source data integration.

## 🌊 Key Features

### Advanced Analytics
- **Multi-source data validation** for enhanced accuracy
- **AI-powered risk assessment** with confidence scoring
- **Interactive flood maps** with real-time updates
- **Professional satellite data display** with acquisition details

### Enhanced User Experience
- **Clean, modern interface** with professional design
- **Improved AI assistant** with quick analysis buttons
- **Real-time data freshness** indicators
- **Comprehensive flood analytics** and metrics

## 🚀 Quick Start

### Option 1: Docker Installation (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd floodscope-ai
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run with Docker:**
   ```bash
   docker-compose up -d
   ```

4. **Access the application:**
   Open http://localhost:5000 in your browser

### Option 2: Local Installation

#### Windows
```bash
./install.bat
```

#### Mac/Linux
```bash
chmod +x install.sh
./install.sh
```

## 📱 How to Use

1. **Select Location:** Click on the map or use the search feature
2. **Run Analysis:** Click "Analyze Flood Risk" to get real-time assessment
3. **View Results:** Check flood risk levels, satellite data, and analytics
4. **Get Insights:** Use the AI assistant for instant analysis and recommendations

## 🛠 Technical Features

- **Multi-sensor Analysis:** Combines Sentinel-1 (radar) and Sentinel-2 (optical) data
- **Real-time Processing:** Live data integration with automatic updates
- **Enhanced Accuracy:** Multi-source validation for reliable flood detection
- **Professional Interface:** Clean, modern design with intuitive navigation
- **Time Accuracy:** Proper IST timezone handling for Indian locations


## 🐳 Docker Configuration

The system includes:
- **Automated health checks** for reliability
- **Persistent data storage** for caching
- **Proper timezone configuration** (Asia/Kolkata)
- **Environment variable management** for API keys

## 📖 Management Commands

### Docker
```bash
# Start the application
docker-compose up -d

# Stop the application
docker-compose down

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Update and rebuild
git pull && docker-compose build && docker-compose up -d
```

### Local Development
```bash
# Activate virtual environment
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate.bat  # Windows

# Run the application
streamlit run app.py --server.port 5000

# Install new dependencies
pip install -r requirements-local.txt
```

## 🌍 Global Coverage

FloodScope AI provides accurate flood monitoring for locations worldwide, with enhanced focus on:
- **Indian subcontinent** with IST timezone support
- **Real-time validation** against actual ground conditions
- **Multi-language support** for international deployment

## 🔧 System Requirements

- **Python 3.8+** for local installation
- **Docker & Docker Compose** for containerized deployment
- **4GB RAM** minimum (8GB recommended)
- **Internet connection** for real-time API access

## 📞 Support

For issues, questions, or feature requests:
1. Check the troubleshooting section in docs
2. Review API key configuration
3. Verify Docker/Python installation
4. Contact support team

## 🎯 Accuracy Improvements

Recent enhancements ensure:
- **Realistic flood risk levels** that match actual conditions
- **Proper time correlation** with weather events
- **Enhanced precipitation detection** for better accuracy
- **Multi-source validation** for reliable assessments

---

**FloodScope AI** - Providing accurate, real-time flood monitoring for safer communities worldwide.
