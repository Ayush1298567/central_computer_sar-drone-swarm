#!/bin/bash

echo "🚁 Mission Commander SAR System - Setup Verification"
echo "=================================================="
echo

# Check project structure
echo "📁 Checking project structure..."
if [ -d "backend/app" ] && [ -d "frontend/src" ]; then
    echo "✅ Project structure complete"
else
    echo "❌ Project structure incomplete"
    exit 1
fi

# Check backend files
echo "🐍 Checking backend setup..."
if [ -f "backend/requirements.txt" ] && [ -f "backend/app/main.py" ]; then
    echo "✅ Backend files present"
else
    echo "❌ Backend files missing"
    exit 1
fi

# Check frontend files
echo "⚛️  Checking frontend setup..."
if [ -f "frontend/package.json" ] && [ -f "frontend/src/App.tsx" ]; then
    echo "✅ Frontend files present"
else
    echo "❌ Frontend files missing"
    exit 1
fi

# Check Docker setup
echo "🐳 Checking Docker setup..."
if [ -f "docker-compose.yml" ]; then
    echo "✅ Docker configuration present"
else
    echo "❌ Docker configuration missing"
    exit 1
fi

echo
echo "🎉 Setup verification complete!"
echo "📋 Next steps:"
echo "   1. Run 'docker-compose up -d' to start all services"
echo "   2. Access frontend at http://localhost:3000"
echo "   3. Access backend API at http://localhost:8000"
echo "   4. View API docs at http://localhost:8000/docs"
echo
echo "🔧 For local development:"
echo "   Backend: cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload"
echo "   Frontend: cd frontend && npm install && npm run dev"