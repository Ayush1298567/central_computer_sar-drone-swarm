# SAR Drone System - Deployment Guide

## Quick Start (Development)

### 1. Backend Setup

```bash
# From project root
cd backend

# Install dependencies (use system Python or create venv)
pip install -r requirements.txt --break-system-packages  # If needed

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python -c "from app.core.database import create_tables; create_tables()"

# Start backend
python start.py
```

Backend runs on: `http://localhost:8000`
API Docs: `http://localhost:8000/docs`

### 2. Frontend Setup

```bash
# From project root
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs on: `http://localhost:3000`

## System Verification

### Test Backend
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": {"status": "healthy"}
}
```

### Test Frontend
Open browser to `http://localhost:3000`
- Should see Dashboard with Mission Commander title
- Navigation should work
- Can create new missions

## Database Initialization

The database is automatically created when you first run the backend. To manually initialize:

```bash
cd backend
python -c "from app.core.database import create_tables; create_tables()"
```

## Common Issues

### Backend Won't Start
- Check Python version (3.10+ required)
- Verify all dependencies installed
- Check port 8000 is not in use
- Review logs in `backend/logs/`

### Frontend Won't Start
- Check Node.js version (18+ required)
- Delete `node_modules` and run `npm install` again
- Check port 3000 is not in use
- Verify backend is running

### Database Errors
- Ensure write permissions in backend directory
- Check DATABASE_URL in .env
- Try deleting `sar_missions.db` and recreating

## Production Deployment

### Backend (Gunicorn + Nginx)
```bash
# Install gunicorn
pip install gunicorn

# Run production server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend (Build + Nginx)
```bash
# Build production bundle
npm run build

# Serve dist/ directory with nginx
```

### Nginx Configuration Example
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Docker Deployment (Future)

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/sar
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=sar
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## System Requirements

### Minimum
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 10GB
- **OS**: Linux/Windows/macOS

### Recommended
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 50GB SSD
- **OS**: Ubuntu 22.04 LTS

## Security Considerations

1. **Change SECRET_KEY** in production
2. **Use HTTPS** for all communications
3. **Enable authentication** for API endpoints
4. **Restrict CORS** origins in production
5. **Use PostgreSQL** instead of SQLite for production
6. **Enable rate limiting** on API endpoints
7. **Regular backups** of database

## Monitoring

### Health Check Endpoints
- Backend: `GET /health`
- Database: Included in health check

### Logging
- Backend logs: `backend/logs/sar_system.log`
- Frontend logs: Browser console
- API access logs: uvicorn/gunicorn logs

## Maintenance

### Database Backup
```bash
# SQLite
cp backend/sar_missions.db backend/sar_missions_backup.db

# PostgreSQL
pg_dump -U user sar > backup.sql
```

### Update Dependencies
```bash
# Backend
pip install -r requirements.txt --upgrade

# Frontend
npm update
```

## Performance Optimization

1. **Database Indexing**: Add indexes for frequently queried fields
2. **Caching**: Use Redis for session/telemetry data
3. **CDN**: Serve static assets from CDN
4. **Compression**: Enable gzip compression
5. **Load Balancing**: Use multiple backend workers

## Scaling

### Horizontal Scaling
- Deploy multiple backend instances behind load balancer
- Use PostgreSQL for shared database
- Use Redis for shared session storage
- WebSocket sticky sessions required

### Vertical Scaling
- Increase worker processes
- Allocate more RAM
- Use faster storage (SSD/NVMe)

---

**System is now ready for deployment and operation!**
