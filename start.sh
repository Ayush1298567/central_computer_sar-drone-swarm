#!/bin/bash

echo "Starting SAR Drone Central Computer System..."

# Check if Redis is running
if ! pgrep -x "redis-server" > /dev/null; then
    echo "Starting Redis..."
    redis-server --daemonize yes
    sleep 2
fi

# Check if Ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama..."
    ollama serve &
    sleep 3
fi

# Check if mistral:7b model is available
if ! ollama list | grep -q "mistral:7b"; then
    echo "Pulling mistral:7b model..."
    ollama pull mistral:7b
fi

# Start the application
echo "Starting the application..."
cd backend
python3 main.py