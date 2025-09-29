#!/bin/bash

# SAR Drone Swarm Central Computer Setup Script

echo "🚁 SAR Drone Swarm Central Computer Setup"
echo "========================================"

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

# Create .env file if it doesn't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creating .env file..."
    cat > backend/.env << EOF
# Database Configuration
DATABASE_URL=sqlite:///./sar_missions.db

# Weather API (optional - get from https://openweathermap.org/api)
WEATHER_API_KEY=

# Ollama AI Configuration (optional)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Security
SECRET_KEY=your-super-secret-key-change-in-production-$(date +%s)

# Application Configuration
DEBUG=True
ALLOWED_HOSTS=["http://localhost:3000", "http://127.0.0.1:3000"]
EOF
    echo "✅ Created backend/.env file"
else
    echo "✅ backend/.env file already exists"
fi

# Start the services
echo "🐳 Starting Docker containers..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Initialize the database
echo "🗄️  Initializing database..."
docker-compose exec backend python init_db.py

if [ $? -eq 0 ]; then
    echo "✅ Database initialized successfully"
else
    echo "❌ Database initialization failed"
    exit 1
fi

# Check if services are running
echo "🔍 Checking service status..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend API is running on http://localhost:8000"
else
    echo "❌ Backend API is not responding"
fi

if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is running on http://localhost:3000"
else
    echo "❌ Frontend is not responding"
fi

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Access your application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo ""
echo "🔧 Useful commands:"
echo "   Start services: docker-compose up -d"
echo "   Stop services: docker-compose down"
echo "   View logs: docker-compose logs -f"
echo "   Rebuild: docker-compose up --build -d"
echo ""
echo "📚 For more information, see the README.md file"
echo ""
echo "Happy SAR operations! 🚁"