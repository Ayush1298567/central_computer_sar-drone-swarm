"""
Common dependencies for API endpoints.
"""

from app.core.database import SessionLocal


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
