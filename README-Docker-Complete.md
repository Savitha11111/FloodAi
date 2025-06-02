# FloodScope AI - Complete Docker Image

## Overview
This is a complete, self-contained Docker image of FloodScope AI with all APIs and functionality built-in. When you run this Docker image, the application will start with all features working perfectly.

## Features Included
- ✅ Real-time flood risk analysis
- ✅ Multi-source data integration (Weather, Elevation, News)
- ✅ Interactive flood mapping
- ✅ AI-powered chat assistant for flood/weather queries
- ✅ Email alert system with detailed reports
- ✅ Historical analysis and trending
- ✅ Downloadable reports and analytics
- ✅ Enhanced confidence scoring system

## Quick Start

### Option 1: Using Docker Compose (Recommended)
```bash
# Clone or download the project
git clone <your-repo-url>
cd floodscope-ai

# Build and run the complete application
docker-compose -f docker-compose.complete.yml up --build

# Application will be available at: http://localhost:5000
```

### Option 2: Using Docker directly
```bash
# Build the image
docker build -t floodscope-ai:complete .

# Run the container
docker run -p 5000:5000 \
  -e OPENWEATHER_API_KEY=your_api_key_here \
  -e GMAIL_USER=your_email@gmail.com \
  -e GMAIL_APP_PASSWORD=your_app_password \
  --name floodscope-ai-app \
  floodscope-ai:complete

# Application will be available at: http://localhost:5000
```

## API Configuration (Optional)

For enhanced functionality, you can provide these API keys:

### Required for Weather Data
```bash
OPENWEATHER_API_KEY=your_openweather_api_key
```

### Optional for Enhanced Features
```bash
AMBEE_API_KEY=your_ambee_api_key      # For advanced flood data
COHERE_API_KEY=your_cohere_api_key    # For AI chat assistant
GMAIL_USER=your_email@gmail.com       # For email alerts
GMAIL_APP_PASSWORD=your_app_password  # For email alerts
```

### Getting API Keys
1. **OpenWeather API**: Sign up at https://openweathermap.org/api (Free tier available)
2. **Ambee API**: Register at https://www.getambee.com/ (Free tier available)
3. **Cohere API**: Get key from https://cohere.ai/ (Free tier available)
4. **Gmail**: Use Gmail App Password for email functionality

## Application Features

### 1. Flood Analysis
- Real-time flood risk assessment for any location
- Multi-source data validation for higher confidence
- Elevation and topography analysis
- Weather pattern integration

### 2. Interactive Mapping
- Live flood risk visualization
- Clickable map interface
- Risk zone highlighting
- Historical overlay capabilities

### 3. AI Chat Assistant
- Natural language queries about flood risks
- Weather and emergency information
- Location-specific advice
- Report generation assistance

### 4. Email Alerts
- Automated flood risk reports
- Subscription management
- Detailed analysis attachments
- Emergency notifications

### 5. Analytics Dashboard
- Historical trend analysis
- Risk metrics and statistics
- Downloadable reports
- Performance tracking

## System Requirements

### Minimum Requirements
- 2GB RAM
- 1 CPU core
- 5GB disk space
- Docker 20.10+ or Docker Compose 2.0+

### Recommended Requirements
- 4GB RAM
- 2 CPU cores
- 10GB disk space
- Stable internet connection for API calls

## Production Deployment

### Environment Variables
Set these in your production environment:
```bash
ENVIRONMENT=production
DEBUG=false
CACHE_TTL=3600
REQUEST_TIMEOUT=30
```

### Health Monitoring
The application includes built-in health checks:
- Health endpoint: `http://localhost:5000/_stcore/health`
- Automatic restart on failure
- Resource monitoring

### Scaling
For high-traffic scenarios:
```bash
# Scale with Docker Compose
docker-compose -f docker-compose.complete.yml up --scale floodscope-ai=3
```

## Data Sources
The application uses multiple data sources for accurate analysis:
- OpenWeather API for meteorological data
- Open Elevation API for topography
- News sources for event validation
- Historical weather patterns
- Government flood monitoring (where available)

## Security
- No external dependencies required
- Secure API key handling
- CORS protection enabled
- Session management included

## Troubleshooting

### Common Issues
1. **Port already in use**: Change port mapping `5001:5000`
2. **API keys not working**: Verify keys are valid and have sufficient quota
3. **Memory issues**: Increase Docker memory allocation to 2GB+

### Logs
View application logs:
```bash
docker logs floodscope-ai-app
```

### Reset Application
```bash
docker-compose -f docker-compose.complete.yml down -v
docker-compose -f docker-compose.complete.yml up --build
```

## Support
For issues or questions:
1. Check application logs
2. Verify API key configuration
3. Ensure minimum system requirements are met
4. Check network connectivity for API calls

## License
This complete Docker image contains all necessary components for FloodScope AI operation.