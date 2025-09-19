#!/bin/bash

# SAR Drone Swarm System Setup Script
# This script sets up the complete development environment

set -e

echo "🚁 SAR Drone Swarm System Setup"
echo "================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16 or higher."
    exit 1
fi

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama is not installed. Installing Ollama for AI capabilities..."
    curl -fsSL https://ollama.ai/install.sh | sh
    echo "✅ Ollama installed successfully"
else
    echo "✅ Ollama is already installed"
fi

echo ""
echo "📦 Setting up Backend..."
echo "========================"

# Create Python virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Backend setup complete"

echo ""
echo "🌐 Setting up Frontend..."
echo "========================="

cd frontend

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

echo "✅ Frontend setup complete"

cd ..

echo ""
echo "🤖 Setting up AI Models..."
echo "=========================="

# Pull required Ollama models
echo "Pulling Ollama models (this may take a while)..."
ollama pull llama2
ollama pull codellama

echo "✅ AI models setup complete"

echo ""
echo "🗄️  Setting up Database..."
echo "=========================="

# Initialize database
source venv/bin/activate
cd backend
python -c "
import asyncio
from app.core.database import init_database

async def setup_db():
    await init_database()
    print('✅ Database initialized successfully')

asyncio.run(setup_db())
"

cd ..

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "To start the system:"
echo ""
echo "1. Start the backend server:"
echo "   source venv/bin/activate"
echo "   cd backend"
echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "2. In another terminal, start the frontend:"
echo "   cd frontend"
echo "   npm start"
echo ""
echo "3. Make sure Ollama is running:"
echo "   ollama serve"
echo ""
echo "4. Access the application at: http://localhost:3000"
echo ""
echo "📚 For more information, see README.md"