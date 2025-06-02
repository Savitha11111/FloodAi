# Use Python 3.11 base image for FloodScope AI Complete
FROM python:3.11

# Set working directory
WORKDIR /app

# Install comprehensive system dependencies
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    gcc \
    g++ \
    curl \
    wget \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libfontconfig1 \
    libxss1 \
    libxtst6 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for GDAL
ENV GDAL_DATA=/usr/share/gdal \
    PROJ_LIB=/usr/share/proj \
    PYTHONUNBUFFERED=1

# Copy requirements first for better caching
COPY requirements-local.txt ./

# Install Python dependencies directly with pip
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-local.txt

# Copy application code
COPY . .

# Create .streamlit directory and config
RUN mkdir -p .streamlit

# Create optimized Streamlit config for Docker
RUN echo '[server]\n\
headless = true\n\
address = "0.0.0.0"\n\
port = 5000\n\
enableCORS = false\n\
enableXsrfProtection = false\n\
maxUploadSize = 200\n\
baseUrlPath = ""\n\
\n\
[browser]\n\
gatherUsageStats = false\n\
\n\
[theme]\n\
base = "light"\n\
primaryColor = "#1f77b4"\n\
backgroundColor = "#ffffff"\n\
secondaryBackgroundColor = "#f0f2f6"\n\
\n\
[logger]\n\
level = "info"' > .streamlit/config.toml

# Create required directories
RUN mkdir -p data logs cache

# Set permissions
RUN chmod -R 755 /app

# Create entrypoint script for better initialization
RUN echo '#!/bin/bash\n\
echo "Starting FloodScope AI Complete Docker Image..."\n\
echo "Initializing services..."\n\
echo "All API integrations are built-in"\n\
echo "Application starting on port 5000"\n\
exec "$@"' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# ----------------------------------------------
# Add application environment variables
# ----------------------------------------------
ENV APP_NAME="FloodScope AI" \
    APP_VERSION="1.0.0" \
    ENVIRONMENT="production" \
    DEBUG=false \
    PORT=5000 \
    HOST=0.0.0.0 \
    OPENWEATHER_API_KEY="8c06e2748683fa98158ae917ff9e5c65" \
    AMBEE_API_KEY="d3df55c0f5b67008dc36940e757a963511f1fd474d0480ef6f8123e5f6edb951" \
    COHERE_API_KEY="WuWBkSf2A5ErNBUTXjRRjCfCgMtIspDfCMeFCRR0" \
    GMAIL_USER="savitha7722@gmail.com" \
    GMAIL_APP_PASSWORD="eoblpsdlpzkdkgcm" \
    CACHE_TTL=3600 \
    MAX_WORKERS=4 \
    REQUEST_TIMEOUT=30 \
    ENABLE_EMAIL_ALERTS=true \
    ENABLE_CHAT_ASSISTANT=true \
    ENABLE_ADVANCED_ANALYSIS=true \
    ENABLE_REAL_TIME_MONITORING=true \
    DEFAULT_LOCATION="Mumbai, India" \
    DEFAULT_COORDINATES="19.0760,72.8777" \
    ANALYSIS_RADIUS_KM=50 \
    LOG_LEVEL=INFO \
    LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s" \
    SESSION_TIMEOUT=3600 \
    CORS_ENABLED=false \
    XSRF_PROTECTION=false

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:5000/_stcore/health || exit 1

# Set entrypoint and command
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["streamlit", "run", "app.py", "--server.port=5000", "--server.address=0.0.0.0", "--server.headless=true"]
