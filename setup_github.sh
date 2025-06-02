#!/bin/bash

echo "🚀 FloodScope AI - GitHub Repository Setup"
echo "=========================================="

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi

# Remove any existing git repository
if [ -d ".git" ]; then
    echo "🔄 Removing existing git repository..."
    rm -rf .git
fi

# Initialize new repository
echo "📁 Initializing new Git repository..."
git init

# Configure git if not already configured
if [ -z "$(git config user.name)" ]; then
    echo "Please enter your Git username:"
    read git_username
    git config user.name "$git_username"
fi

if [ -z "$(git config user.email)" ]; then
    echo "Please enter your Git email:"
    read git_email
    git config user.email "$git_email"
fi

# Add all files
echo "📦 Adding all project files..."
git add .

# Create initial commit
echo "💾 Creating initial commit..."
git commit -m "Initial commit: FloodScope AI - Advanced Flood Detection System

Features:
- Real-time flood risk assessment using Ambee API
- Multi-source data validation with weather correlation
- Interactive flood mapping with Folium
- AI-powered analysis and chat assistant
- Satellite imagery processing (Sentinel-1/2)
- Docker deployment support
- Enhanced accuracy with precipitation tracking
- Global coverage with timezone support"

# Add remote repository
echo "🌐 Adding GitHub remote repository..."
git remote add origin https://github.com/Savitha11111/floodscopeweb.git

# Set main branch
echo "🔧 Setting up main branch..."
git branch -M main

# Push to GitHub
echo "🚀 Pushing to GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed FloodScope AI to GitHub!"
    echo "🌐 Repository URL: https://github.com/Savitha11111/floodscopeweb"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Visit your repository on GitHub"
    echo "2. Add a description and topics in repository settings"
    echo "3. Configure GitHub Pages if you want to host documentation"
    echo "4. Set up GitHub Actions for CI/CD (optional)"
else
    echo "❌ Failed to push to GitHub. Please check your credentials and try again."
fi