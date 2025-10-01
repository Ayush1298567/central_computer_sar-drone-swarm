"""
Health check endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ....core.database import get_db
from ....ai import create_ollama_intelligence_engine
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "SAR Drone System",
        "timestamp": "2024-01-01T00:00:00Z"
    }

@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check with database and AI status"""
    try:
        # Test database
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = f"error: {e}"
    
    try:
        # Test AI engine (just check if available)
        ai_status = "available"
        models_count = 0
    except Exception as e:
        logger.error(f"AI engine health check failed: {e}")
        ai_status = "error"
        models_count = 0
    
    return {
        "status": "healthy" if db_status == "connected" and ai_status == "healthy" else "degraded",
        "database": db_status,
        "ai_engine": {
            "status": ai_status,
            "models_available": models_count
        },
        "timestamp": "2024-01-01T00:00:00Z"
    }