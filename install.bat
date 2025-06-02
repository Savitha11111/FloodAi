@echo off
REM FloodScope AI - Windows Installation Script

echo 🌊 FloodScope AI - Local Installation Script
echo ============================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python found
python --version

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements-local.txt

REM Create .streamlit directory
echo ⚙️  Setting up Streamlit configuration...
if not exist .streamlit mkdir .streamlit

REM Create Streamlit config
echo [server] > .streamlit\config.toml
echo headless = true >> .streamlit\config.toml
echo address = "0.0.0.0" >> .streamlit\config.toml
echo port = 5000 >> .streamlit\config.toml
echo. >> .streamlit\config.toml
echo [browser] >> .streamlit\config.toml
echo gatherUsageStats = false >> .streamlit\config.toml

REM Create .env file if it doesn't exist
if not exist .env (
    echo 🔑 Creating environment file...
    echo # FloodScope AI - Enhanced Environment Configuration > .env
    echo # Real-time Weather Data API >> .env
    echo OPENWEATHER_API_KEY=your_openweather_api_key_here >> .env
    echo. >> .env
    echo # Real-time Flood Monitoring API >> .env
    echo AMBEE_API_KEY=your_ambee_api_key_here >> .env
    echo. >> .env
    echo # Satellite Imagery APIs >> .env
    echo SENTINELHUB_CLIENT_ID=your_sentinelhub_client_id_here >> .env
    echo SENTINELHUB_CLIENT_SECRET=your_sentinelhub_client_secret_here >> .env
    echo ⚠️  Please edit .env file and add your API keys before running the application
    echo.
    echo 📖 API Key Sources:
    echo   - OpenWeather: https://openweathermap.org/api
    echo   - Ambee: https://www.getambee.com/
    echo   - Sentinel Hub: https://apps.sentinel-hub.com/
) else (
    echo ✅ Environment file already exists
)

echo.
echo 🎉 Installation completed successfully!
echo.
echo Next steps:
echo 1. Edit .env file with your API keys
echo 2. Run: venv\Scripts\activate.bat
echo 3. Run: streamlit run app.py --server.port 5000
echo.
echo The application will be available at: http://localhost:5000
echo.
pause