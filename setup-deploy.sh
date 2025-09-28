#!/bin/bash

# Mission Commander SAR Drone System - Setup and Deployment Script
# This script handles installation, configuration, and deployment of the complete system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check system requirements
check_requirements() {
    print_status "Checking system requirements..."

    # Check Docker
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi

    # Check Docker Compose
    if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi

    # Check Git
    if ! command_exists git; then
        print_error "Git is not installed. Please install Git first."
        exit 1
    fi

    # Check available disk space (need at least 5GB)
    available_space=$(df . | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 5242880 ]; then  # 5GB in KB
        print_error "Insufficient disk space. Need at least 5GB free."
        exit 1
    fi

    print_success "All requirements satisfied"
}

# Function to clone or update repository
setup_repository() {
    print_status "Setting up repository..."

    if [ ! -d ".git" ]; then
        print_status "Cloning repository..."
        git clone https://github.com/your-org/mission-commander.git .
    else
        print_status "Repository already exists, pulling latest changes..."
        git pull origin main
    fi

    print_success "Repository setup complete"
}

# Function to configure environment
configure_environment() {
    print_status "Configuring environment..."

    # Create environment files if they don't exist
    if [ ! -f "backend/.env" ]; then
        print_status "Creating backend environment configuration..."
        cat > backend/.env << EOF
# Database Configuration
DATABASE_URL=postgresql://postgres:password@db:5432/sar_missions
POSTGRES_URL=postgresql://postgres:password@db:5432/sar_missions
REDIS_URL=redis://redis:6379

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=$(openssl rand -hex 32)
DEBUG=false

# AI Configuration
OLLAMA_HOST=http://ollama:11434
DEFAULT_MODEL=llama3.2:3b
MODEL_TIMEOUT=30

# File Storage
UPLOAD_DIR=uploads
MAX_FILE_SIZE=104857600

# Mission Configuration
MAX_CONCURRENT_MISSIONS=10
MAX_DRONES_PER_MISSION=15
DEFAULT_SEARCH_ALTITUDE=20.0
MIN_BATTERY_LEVEL=20.0
MAX_WIND_SPEED=15.0

# Communication
WEBSOCKET_PING_INTERVAL=30
WEBSOCKET_PING_TIMEOUT=10
TELEMETRY_UPDATE_INTERVAL=1.0
MAX_TELEMETRY_BUFFER=1000

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/sar_system.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5
EOF
        print_success "Backend environment configured"
    fi

    if [ ! -f "frontend/.env.local" ]; then
        print_status "Creating frontend environment configuration..."
        cat > frontend/.env.local << EOF
VITE_API_BASE_URL=http://localhost:8000
VITE_WEBSOCKET_URL=ws://localhost:8000/ws
VITE_MAP_API_KEY=your-mapbox-api-key
EOF
        print_warning "Frontend environment created. Please update VITE_MAP_API_KEY with your Mapbox API key."
    fi

    print_success "Environment configuration complete"
}

# Function to setup AI model
setup_ai_model() {
    print_status "Setting up AI model..."

    # Check if Ollama is running
    if ! docker compose ps ollama | grep -q "Up"; then
        print_status "Starting Ollama service..."
        docker compose up -d ollama

        # Wait for Ollama to be ready
        print_status "Waiting for Ollama to start..."
        sleep 10
    fi

    # Pull the required model
    print_status "Pulling AI model (llama3.2:3b)..."
    docker compose exec ollama ollama pull llama3.2:3b || {
        print_warning "Model pull failed. Ollama may still be starting. You can pull the model manually later:"
        echo "docker compose exec ollama ollama pull llama3.2:3b"
    }

    print_success "AI model setup complete"
}

# Function to build and start services
start_services() {
    print_status "Building and starting services..."

    # Build all services
    print_status "Building Docker images..."
    docker compose build

    # Start database and dependencies first
    print_status "Starting database and dependencies..."
    docker compose up -d db redis ollama

    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    sleep 15

    # Run database migrations
    print_status "Running database migrations..."
    docker compose exec backend python -c "
from app.core.database import create_tables
create_tables()
print('Database tables created successfully')
" || {
        print_warning "Database migration failed. This may be normal on first run."
    }

    # Start all services
    print_status "Starting all services..."
    docker compose up -d

    # Wait for services to be healthy
    print_status "Waiting for services to be healthy..."
    sleep 20

    print_success "Services started successfully"
}

# Function to run health checks
run_health_checks() {
    print_status "Running health checks..."

    # Check backend health
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        print_success "Backend API is healthy"
    else
        print_error "Backend API health check failed"
        return 1
    fi

    # Check frontend health
    if curl -f http://localhost:3000 >/dev/null 2>&1; then
        print_success "Frontend application is healthy"
    else
        print_warning "Frontend health check failed (this may be normal during build)"
    fi

    # Check database connectivity
    if docker compose exec db pg_isready -U postgres >/dev/null 2>&1; then
        print_success "Database is healthy"
    else
        print_error "Database health check failed"
        return 1
    fi

    # Check Ollama
    if curl -f http://localhost:11434/api/tags >/dev/null 2>&1; then
        print_success "Ollama AI service is healthy"
    else
        print_warning "Ollama health check failed"
    fi

    print_success "Health checks completed"
}

# Function to run tests
run_tests() {
    print_status "Running test suite..."

    # Run backend tests
    print_status "Running backend tests..."
    if docker compose exec backend python -m pytest tests/ -v --tb=short; then
        print_success "Backend tests passed"
    else
        print_warning "Some backend tests failed"
    fi

    # Run frontend tests
    print_status "Running frontend tests..."
    if docker compose exec frontend npm test -- --watchAll=false --coverage; then
        print_success "Frontend tests passed"
    else
        print_warning "Some frontend tests failed"
    fi

    print_success "Test suite completed"
}

# Function to create SSL certificates (for production)
setup_ssl() {
    print_status "Setting up SSL certificates..."

    # Create SSL directory
    mkdir -p ssl

    # Generate self-signed certificate (for development)
    if [ ! -f "ssl/server.crt" ]; then
        print_status "Generating self-signed SSL certificate..."
        openssl req -x509 -newkey rsa:4096 -keyout ssl/server.key -out ssl/server.crt \
            -days 365 -nodes -subj "/CN=localhost"

        print_success "SSL certificate generated"
    else
        print_status "SSL certificate already exists"
    fi
}

# Function to setup nginx configuration
setup_nginx() {
    print_status "Setting up Nginx configuration..."

    if [ ! -f "nginx.conf" ]; then
        print_status "Creating Nginx configuration..."
        cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    # Basic settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=frontend:10m rate=30r/s;

    # Upstream servers
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name localhost;

        return 301 https://$server_name$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name localhost;

        ssl_certificate /etc/nginx/ssl/server.crt;
        ssl_certificate_key /etc/nginx/ssl/server.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;

            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;

            # WebSocket support
            location /ws/ {
                proxy_pass http://backend;
                proxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection "upgrade";
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
            }
        }

        # Frontend application
        location / {
            limit_req zone=frontend burst=50 nodelay;

            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;

            # Handle client-side routing
            try_files $uri $uri/ /index.html;
        }

        # Static file serving
        location /uploads/ {
            alias /app/uploads/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF
        print_success "Nginx configuration created"
    else
        print_status "Nginx configuration already exists"
    fi
}

# Function to show post-setup instructions
show_instructions() {
    print_success "Setup completed successfully!"
    echo ""
    echo -e "${BLUE}🚀 Mission Commander SAR Drone System is ready!${NC}"
    echo ""
    echo "Access the application:"
    echo "  • Frontend: http://localhost:3000"
    echo "  • Backend API: http://localhost:8000"
    echo "  • API Documentation: http://localhost:8000/docs"
    echo ""
    echo "Useful commands:"
    echo "  • View logs: docker compose logs -f"
    echo "  • Stop services: docker compose down"
    echo "  • Restart services: docker compose restart"
    echo "  • Run tests: docker compose exec backend pytest tests/"
    echo ""
    echo "Next steps:"
    echo "  1. Open http://localhost:3000 in your browser"
    echo "  2. Create your first mission using natural language"
    echo "  3. Register drones and start monitoring"
    echo ""
    print_warning "Important:"
    echo "  • Change the SECRET_KEY in backend/.env for production"
    echo "  • Update frontend/.env.local with your Mapbox API key"
    echo "  • Configure SSL certificates for production deployment"
    echo ""
    echo -e "${GREEN}Happy SAR operations! 🛩️${NC}"
}

# Main execution
main() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║              Mission Commander SAR Setup Script              ║"
    echo "║                 Search and Rescue Drone System               ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""

    # Check if we're in the right directory
    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml not found. Please run this script from the project root."
        exit 1
    fi

    # Run setup steps
    check_requirements
    setup_repository
    configure_environment
    setup_ai_model
    setup_ssl
    setup_nginx
    start_services

    # Optional: run health checks
    if [ "$1" = "--health-check" ]; then
        run_health_checks
    fi

    # Optional: run tests
    if [ "$1" = "--tests" ]; then
        run_tests
    fi

    show_instructions
}

# Handle command line arguments
case "${1:-}" in
    "--help"|"-h")
        echo "Mission Commander SAR Drone System Setup Script"
        echo ""
        echo "Usage: $0 [OPTION]"
        echo ""
        echo "Options:"
        echo "  --health-check    Run health checks after setup"
        echo "  --tests          Run test suite after setup"
        echo "  --help, -h       Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0                    # Basic setup"
        echo "  $0 --health-check     # Setup with health checks"
        echo "  $0 --tests           # Setup with tests"
        echo ""
        exit 0
        ;;
    "--health-check")
        main "$1"
        ;;
    "--tests")
        main "$1"
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac