@echo off
echo 🌊 FloodScope AI - Single Command Docker Deployment
echo ==================================================

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

echo ✅ Docker is running

REM Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file with default values...
    echo # FloodScope AI - Environment Configuration > .env
    echo OPENWEATHER_API_KEY=your_openweather_api_key_here >> .env
    echo AMBEE_API_KEY=your_ambee_api_key_here >> .env
    echo SENTINELHUB_CLIENT_ID=your_sentinelhub_client_id_here >> .env
    echo SENTINELHUB_CLIENT_SECRET=your_sentinelhub_client_secret_here >> .env
    echo ⚠️  Edit .env file with your API keys for full functionality
)

REM Stop any existing container
echo 🛑 Stopping any existing FloodScope containers...
docker-compose down 2>nul

REM Build and run
echo 🔨 Building FloodScope AI Docker image...
docker-compose build

if %errorlevel% equ 0 (
    echo 🚀 Starting FloodScope AI...
    docker-compose up -d
    
    if %errorlevel% equ 0 (
        echo.
        echo ✅ FloodScope AI is now running!
        echo 🌐 Access your application at: http://localhost:5000
        echo.
        echo 📊 Commands:
        echo   View logs: docker-compose logs -f
        echo   Stop app:  docker-compose down
        echo   Restart:   docker-compose restart
        echo.
        echo ⏳ Please wait 30-60 seconds for the application to fully load...
        pause
    ) else (
        echo ❌ Failed to start FloodScope AI
        pause
        exit /b 1
    )
) else (
    echo ❌ Failed to build FloodScope AI
    pause
    exit /b 1
)