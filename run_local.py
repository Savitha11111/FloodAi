#!/usr/bin/env python3
"""
FloodScope AI - Local Debug Runner
This script helps diagnose issues when running locally
"""

import sys
import os

def check_python_version():
    """Check if Python version is compatible"""
    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print("✅ Python version OK")
    return True

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'streamlit',
        'pandas',
        'numpy',
        'requests',
        'folium',
        'streamlit_folium',
        'plotly',
        'PIL',
        'pytz'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'PIL':
                import PIL
            elif package == 'streamlit_folium':
                import streamlit_folium
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    return missing_packages

def check_environment():
    """Check environment variables"""
    env_vars = [
        'OPENWEATHER_API_KEY',
        'AMBEE_API_KEY', 
        'SENTINELHUB_CLIENT_ID',
        'SENTINELHUB_CLIENT_SECRET'
    ]
    
    missing_vars = []
    for var in env_vars:
        if os.getenv(var):
            print(f"✅ {var} is set")
        else:
            print(f"⚠️  {var} - NOT SET")
            missing_vars.append(var)
    
    return missing_vars

def check_files():
    """Check if required files exist"""
    required_files = [
        'app.py',
        'requirements-local.txt',
        '.env'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")
            missing_files.append(file)
    
    return missing_files

def main():
    print("🌊 FloodScope AI - Local Environment Check")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return
    
    print("\n📦 Checking Dependencies:")
    missing_packages = check_dependencies()
    
    print("\n🔑 Checking Environment Variables:")
    missing_vars = check_environment()
    
    print("\n📁 Checking Required Files:")
    missing_files = check_files()
    
    print("\n" + "=" * 50)
    
    if missing_packages:
        print("❌ MISSING PACKAGES:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nTo install missing packages:")
        print("pip install -r requirements-local.txt")
    
    if missing_files:
        print("❌ MISSING FILES:")
        for file in missing_files:
            print(f"   - {file}")
    
    if missing_vars:
        print("⚠️  MISSING ENVIRONMENT VARIABLES:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nEdit .env file and add your API keys")
    
    if not missing_packages and not missing_files:
        print("✅ All checks passed! Try running:")
        print("streamlit run app.py --server.port 5000")
    
    print("\n🔧 If you still see a blank page, check the terminal for error messages")

if __name__ == "__main__":
    main()