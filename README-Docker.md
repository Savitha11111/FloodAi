# FloodScope AI - Docker Deployment Guide

## Quick Start

### Prerequisites
- Docker installed on your system
- Docker Compose (included with Docker Desktop)
- Your API keys ready:
  - Ambee API Key
  - OpenWeather API Key

### Environment Setup

1. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Add your API keys to `.env` file:**
   ```
   AMBEE_API_KEY=your_ambee_api_key_here
   OPENWEATHER_API_KEY=your_openweather_api_key_here
   ```

### Running with Docker Compose (Recommended)

```bash
# Build and start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

The application will be available at: http://localhost:5000

### Running with Docker directly

```bash
# Build the image
docker build -t floodscope-ai .

# Run the container
docker run -d \
  --name floodscope \
  -p 5000:5000 \
  --env-file .env \
  floodscope-ai

# View logs
docker logs -f floodscope

# Stop the container
docker stop floodscope
```

## Production Deployment

### Environment Variables
- `AMBEE_API_KEY`: Your Ambee API key for real-time flood data
- `OPENWEATHER_API_KEY`: Your OpenWeather API key for weather data

### Health Monitoring
The container includes health checks:
```bash
# Check container health
docker ps
```

### Updating the Application
```bash
# Pull latest changes and rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Troubleshooting

### Common Issues

1. **Container fails to start:**
   - Check if API keys are properly set in `.env` file
   - Ensure port 5000 is not already in use

2. **API errors:**
   - Verify your Ambee and OpenWeather API keys are valid
   - Check API rate limits

3. **Performance issues:**
   - Increase container memory if needed:
     ```yaml
     services:
       floodscope:
         deploy:
           resources:
             limits:
               memory: 2G
     ```

### Logs and Debugging
```bash
# View application logs
docker-compose logs floodscope

# Access container shell for debugging
docker-compose exec floodscope /bin/bash
```

## Features
- ✅ Real-time flood risk assessment
- ✅ Enhanced precipitation tracking  
- ✅ Multi-source data validation
- ✅ Interactive flood mapping
- ✅ Accurate global coverage
- ✅ Docker containerized deployment