#!/bin/bash

# SAR Mission Commander Setup Script

echo "🚁 SAR Mission Commander Setup"
echo "=============================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Initialize the database
echo "📊 Initializing database..."
cd backend
python3 init_db.py
cd ..

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend API is running on http://localhost:8000"
else
    echo "❌ Backend API is not responding. Check the logs with: docker-compose logs backend"
fi

if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is running on http://localhost:3000"
else
    echo "❌ Frontend is not responding. Check the logs with: docker-compose logs frontend"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "🌐 Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo ""
echo "📖 For more information, see the README.md file"
echo ""
echo "🛑 To stop the services: docker-compose down"