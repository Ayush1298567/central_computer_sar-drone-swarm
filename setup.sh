#!/bin/bash

echo "Setting up SAR Drone Central Computer System..."

# Check if Python 3.10+ is installed
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.10+ is required. Current version: $python_version"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is required but not installed."
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Check if Redis is installed
if ! command -v redis-server &> /dev/null; then
    echo "Error: Redis is required but not installed."
    echo "Please install Redis:"
    echo "  Ubuntu/Debian: sudo apt-get install redis-server"
    echo "  macOS: brew install redis"
    echo "  Or download from https://redis.io/download"
    exit 1
fi

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Warning: Ollama is not installed. Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install Ollama. Please install manually from https://ollama.ai/"
        exit 1
    fi
fi

echo "Installing Python dependencies..."
cd backend
pip3 install -r ../requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install Python dependencies"
    exit 1
fi

echo "Installing Node.js dependencies..."
cd ../frontend
npm install
if [ $? -ne 0 ]; then
    echo "Error: Failed to install Node.js dependencies"
    exit 1
fi

echo "Building React frontend..."
npm run build
if [ $? -ne 0 ]; then
    echo "Error: Failed to build React frontend"
    exit 1
fi

cd ..

echo "Setting up Ollama model..."
ollama pull mistral:7b
if [ $? -ne 0 ]; then
    echo "Warning: Failed to pull mistral:7b model. You may need to do this manually."
fi

echo "Creating necessary directories..."
mkdir -p logs
mkdir -p data

echo "Setup complete!"
echo ""
echo "To start the system:"
echo "1. Start Redis: redis-server"
echo "2. Start Ollama: ollama serve"
echo "3. Start the application: python3 backend/main.py"
echo ""
echo "Then open http://localhost:8000 in your browser"