#!/bin/bash

# SAR Drone System Setup Script
# This script sets up the complete SAR drone swarm control system

set -e  # Exit on any error

echo "🚀 SAR Drone Swarm Control System Setup"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command_exists python3; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

if ! command_exists pip3; then
    echo "❌ pip3 is required but not installed"
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

if ! command_exists npm; then
    echo "❌ npm is required but not installed"
    exit 1
fi

echo "✅ All prerequisites found"

# Setup backend
echo ""
echo "🔧 Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env configuration file..."
    cat > .env << EOF
# Database
DATABASE_URL=sqlite:///./sar_drone.db

# Security
SECRET_KEY=sar-drone-secret-key-change-in-production-min-32-chars-long

# AI
OLLAMA_HOST=http://localhost:11434
DEFAULT_MODEL=llama3.2:3b
OPENAI_API_KEY=

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Drone Configuration
MAX_DRONES=10
DEFAULT_ALTITUDE=50
DEFAULT_SPEED=5.0

# Emergency Settings
LOW_BATTERY_THRESHOLD=20.0
CRITICAL_BATTERY_THRESHOLD=15.0
COMMUNICATION_TIMEOUT=30

# Logging
LOG_LEVEL=INFO
DEBUG=true
EOF
    echo "✅ Created .env file"
else
    echo "✅ .env file already exists"
fi

# Initialize database
echo "Initializing database..."
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from app.core.database import init_db
asyncio.run(init_db())
print('Database initialized successfully')
"

echo "✅ Backend setup complete"

# Setup frontend
echo ""
echo "🔧 Setting up frontend..."
cd ../frontend

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

# Create .env file for frontend
if [ ! -f ".env" ]; then
    echo "Creating frontend .env file..."
    cat > .env << EOF
VITE_WS_URL=ws://localhost:8000/ws
VITE_API_URL=http://localhost:8000/api/v1
EOF
    echo "✅ Created frontend .env file"
else
    echo "✅ Frontend .env file already exists"
fi

echo "✅ Frontend setup complete"

# Run validation tests
echo ""
echo "🧪 Running validation tests..."
cd ../backend
source venv/bin/activate

# Run the validation script
python3 run_tests.py

# Check if tests passed
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 SETUP COMPLETE!"
    echo "=================="
    echo ""
    echo "✅ All systems are ready for deployment"
    echo ""
    echo "🚀 To start the system:"
    echo ""
    echo "Backend:"
    echo "  cd backend"
    echo "  source venv/bin/activate"
    echo "  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    echo ""
    echo "Frontend:"
    echo "  cd frontend"
    echo "  npm run dev"
    echo ""
    echo "🌐 Access the system at:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend API: http://localhost:8000"
    echo "  API Docs: http://localhost:8000/docs"
    echo ""
    echo "🤖 Optional AI Setup:"
    echo "  Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh"
    echo "  Pull model: ollama pull llama3.2:3b"
    echo ""
    echo "⚠️  Remember: This system is designed for life-saving SAR operations!"
    echo "   Ensure all components are properly tested before deployment."
else
    echo ""
    echo "⚠️  SETUP COMPLETED WITH ISSUES"
    echo "==============================="
    echo ""
    echo "Some tests failed. Please check the output above and:"
    echo "1. Install missing dependencies"
    echo "2. Check configuration files"
    echo "3. Verify database connectivity"
    echo "4. Run tests again: python3 run_tests.py"
    echo ""
    echo "The system may still be functional for basic operations."
fi

echo ""
echo "📚 For more information, see README.md"
echo "🆘 For troubleshooting, check the logs and error messages above"