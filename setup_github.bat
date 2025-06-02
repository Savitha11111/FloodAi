@echo off
echo FloodScope AI - GitHub Repository Setup
echo ==========================================

REM Check if git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Git is not installed. Please install Git first.
    pause
    exit /b 1
)

REM Remove existing git repository
if exist ".git" (
    echo Removing existing git repository...
    rmdir /s /q .git
)

REM Initialize new repository
echo Initializing new Git repository...
git init

REM Add all files
echo Adding all project files...
git add .

REM Create initial commit
echo Creating initial commit...
git commit -m "Initial commit: FloodScope AI - Advanced Flood Detection System"

REM Add remote repository
echo Adding GitHub remote repository...
git remote add origin https://github.com/Savitha11111/floodscopeweb.git

REM Set main branch
echo Setting up main branch...
git branch -M main

REM Push to GitHub
echo Pushing to GitHub...
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo Successfully pushed FloodScope AI to GitHub!
    echo Repository URL: https://github.com/Savitha11111/floodscopeweb
    echo.
    echo Next Steps:
    echo 1. Visit your repository on GitHub
    echo 2. Add a description and topics in repository settings
    echo 3. Configure environment variables for deployment
) else (
    echo Failed to push to GitHub. Please check your credentials and try again.
)

pause