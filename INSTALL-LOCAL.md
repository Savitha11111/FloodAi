# FloodScope AI - Local Installation Guide

## Prerequisites

### For Windows:
- Python 3.8+ installed ([Download Python](https://www.python.org/downloads/))
- Git installed ([Download Git](https://git-scm.com/download/win))
- Visual Studio Build Tools (for some packages)

### For Mac:
- Python 3.8+ installed (use Homebrew: `brew install python`)
- Git installed (usually pre-installed or via Xcode Command Line Tools)
- Xcode Command Line Tools: `xcode-select --install`

## Installation Steps

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd floodscope-ai
```

### 2. Create Virtual Environment

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements-local.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root:

**Windows (Command Prompt):**
```cmd
copy nul .env
```

**Mac/Linux:**
```bash
touch .env
```

Add your API keys to the `.env` file:
```
AMBEE_API_KEY=your_ambee_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here
```

### 5. Create Streamlit Configuration

Create `.streamlit` directory and config file:

**Windows:**
```cmd
mkdir .streamlit
echo [server] > .streamlit\config.toml
echo headless = true >> .streamlit\config.toml
echo address = "0.0.0.0" >> .streamlit\config.toml
echo port = 5000 >> .streamlit\config.toml
```

**Mac/Linux:**
```bash
mkdir -p .streamlit
cat > .streamlit/config.toml << EOF
[server]
headless = true
address = "0.0.0.0"
port = 5000
EOF
```

### 6. Run the Application

```bash
streamlit run app.py --server.port 5000
```

The application will be available at: http://localhost:5000

## API Keys Setup

### Getting Your API Keys:

1. **Ambee API Key:**
   - Visit [Ambee Data](https://www.ambeedata.com/)
   - Sign up for an account
   - Get your API key from the dashboard

2. **OpenWeather API Key:**
   - Visit [OpenWeatherMap](https://openweathermap.org/api)
   - Sign up for a free account
   - Get your API key from your account dashboard

## Troubleshooting

### Common Issues:

#### Windows Specific:
1. **"Microsoft Visual C++ 14.0 is required" error:**
   - Install Microsoft C++ Build Tools
   - Or install Visual Studio Community

2. **Permission denied errors:**
   - Run Command Prompt as Administrator
   - Or use PowerShell with execution policy: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

#### Mac Specific:
1. **"Command not found" errors:**
   - Make sure Python is in your PATH
   - Use `python3` instead of `python` if needed

2. **Permission errors:**
   - Use `sudo` for system-wide installations (not recommended for virtual environments)

#### General Issues:
1. **Port 5000 already in use:**
   ```bash
   streamlit run app.py --server.port 8501
   ```

2. **Module import errors:**
   - Ensure virtual environment is activated
   - Reinstall requirements: `pip install -r requirements-local.txt`

3. **API connection errors:**
   - Verify your API keys are correct in `.env` file
   - Check your internet connection
   - Verify API rate limits

### Development Mode:

For development with auto-reload:
```bash
streamlit run app.py --server.runOnSave true
```

## Project Structure
```
floodscope-ai/
├── app.py                 # Main application
├── services/             # API services
│   ├── ambee_flood_service.py
│   ├── weather_service.py
│   └── ...
├── utils/                # Utility functions
├── .env                  # Environment variables (create this)
├── .streamlit/           # Streamlit configuration
├── requirements-local.txt # Python dependencies
└── README-Docker.md      # Docker deployment guide
```

## Next Steps

1. **Test the application** with different locations
2. **Verify API connections** are working correctly
3. **Check data accuracy** for your local areas
4. **Customize settings** in `.streamlit/config.toml` if needed

## Getting Help

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all prerequisites are installed
3. Ensure API keys are valid and have sufficient quota
4. Check the application logs for detailed error messages