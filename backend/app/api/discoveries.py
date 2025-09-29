"""
Discovery management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from ..core.database import get_db
from ..models import Discovery
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_discoveries(
    skip: int = 0,
    limit: int = 100,
    mission_id: Optional[int] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    discovery_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all discoveries with optional filtering."""
    query = db.query(Discovery)

    if mission_id:
        query = query.filter(Discovery.mission_id == mission_id)
    if status:
        query = query.filter(Discovery.status == status)
    if priority:
        query = query.filter(Discovery.priority == priority)
    if discovery_type:
        query = query.filter(Discovery.discovery_type == discovery_type)

    discoveries = query.offset(skip).limit(limit).all()
    return discoveries


@router.get("/{discovery_id}")
async def get_discovery(discovery_id: int, db: Session = Depends(get_db)):
    """Get a specific discovery by ID."""
    discovery = db.query(Discovery).filter(Discovery.id == discovery_id).first()
    if not discovery:
        raise HTTPException(status_code=404, detail="Discovery not found")
    return discovery


@router.post("/")
async def create_discovery(discovery_data: dict, db: Session = Depends(get_db)):
    """Create a new discovery."""
    try:
        discovery = Discovery(**discovery_data)
        db.add(discovery)
        db.commit()
        db.refresh(discovery)

        logger.info(f"Created discovery: {discovery.discovery_type} (ID: {discovery.id})")
        return discovery
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating discovery: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{discovery_id}")
async def update_discovery(
    discovery_id: int,
    discovery_data: dict,
    db: Session = Depends(get_db)
):
    """Update an existing discovery."""
    discovery = db.query(Discovery).filter(Discovery.id == discovery_id).first()
    if not discovery:
        raise HTTPException(status_code=404, detail="Discovery not found")

    try:
        for key, value in discovery_data.items():
            setattr(discovery, key, value)

        discovery.updated_at = "2024-01-01T00:00:00Z"  # Would be current timestamp
        db.commit()
        db.refresh(discovery)

        logger.info(f"Updated discovery: {discovery.discovery_type} (ID: {discovery.id})")
        return discovery
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating discovery: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{discovery_id}")
async def delete_discovery(discovery_id: int, db: Session = Depends(get_db)):
    """Delete a discovery."""
    discovery = db.query(Discovery).filter(Discovery.id == discovery_id).first()
    if not discovery:
        raise HTTPException(status_code=404, detail="Discovery not found")

    try:
        db.delete(discovery)
        db.commit()
        logger.info(f"Deleted discovery: {discovery.discovery_type} (ID: {discovery.id})")
        return {"message": "Discovery deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting discovery: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{discovery_id}/investigate")
async def investigate_discovery(discovery_id: int, db: Session = Depends(get_db)):
    """Mark a discovery as being investigated."""
    discovery = db.query(Discovery).filter(Discovery.id == discovery_id).first()
    if not discovery:
        raise HTTPException(status_code=404, detail="Discovery not found")

    try:
        discovery.status = "investigating"
        discovery.investigated_at = "2024-01-01T00:00:00Z"  # Would be current timestamp
        db.commit()

        logger.info(f"Started investigation of discovery: {discovery.discovery_type} (ID: {discovery.id})")
        return {"message": "Investigation started", "discovery": discovery}
    except Exception as e:
        db.rollback()
        logger.error(f"Error starting investigation: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{discovery_id}/resolve")
async def resolve_discovery(
    discovery_id: int,
    resolution: dict,
    db: Session = Depends(get_db)
):
    """Resolve a discovery with investigation results."""
    discovery = db.query(Discovery).filter(Discovery.id == discovery_id).first()
    if not discovery:
        raise HTTPException(status_code=404, detail="Discovery not found")

    try:
        # Update discovery with resolution data
        if "status" in resolution:
            discovery.status = resolution["status"]
        if "investigation_notes" in resolution:
            discovery.investigation_notes = resolution["investigation_notes"]
        if "response_required" in resolution:
            discovery.response_required = resolution["response_required"]

        discovery.resolved_at = "2024-01-01T00:00:00Z"  # Would be current timestamp
        db.commit()

        logger.info(f"Resolved discovery: {discovery.discovery_type} (ID: {discovery.id})")
        return {"message": "Discovery resolved", "discovery": discovery}
    except Exception as e:
        db.rollback()
        logger.error(f"Error resolving discovery: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{discovery_id}/upload-media")
async def upload_discovery_media(
    discovery_id: int,
    media_type: str,  # image, video, audio
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload media file for a discovery."""
    discovery = db.query(Discovery).filter(Discovery.id == discovery_id).first()
    if not discovery:
        raise HTTPException(status_code=404, detail="Discovery not found")

    try:
        # Create uploads directory if it doesn't exist
        upload_dir = "uploads/discoveries"
        os.makedirs(upload_dir, exist_ok=True)

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{discovery_id}_{timestamp}_{file.filename}"
        file_path = os.path.join(upload_dir, filename)

        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Update discovery with media path
        if media_type == "image":
            discovery.image_path = file_path
        elif media_type == "video":
            discovery.video_path = file_path
        elif media_type == "audio":
            discovery.audio_path = file_path

        db.commit()

        logger.info(f"Uploaded {media_type} for discovery: {discovery.discovery_type} (ID: {discovery.id})")
        return {
            "message": f"{media_type.title()} uploaded successfully",
            "file_path": file_path,
            "discovery": discovery
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading media: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{discovery_id}/media/{media_type}")
async def get_discovery_media(
    discovery_id: int,
    media_type: str,  # image, video, audio
    db: Session = Depends(get_db)
):
    """Get media file path for a discovery."""
    discovery = db.query(Discovery).filter(Discovery.id == discovery_id).first()
    if not discovery:
        raise HTTPException(status_code=404, detail="Discovery not found")

    media_path = None
    if media_type == "image":
        media_path = discovery.image_path
    elif media_type == "video":
        media_path = discovery.video_path
    elif media_type == "audio":
        media_path = discovery.audio_path

    if not media_path:
        raise HTTPException(status_code=404, detail=f"No {media_type} found for this discovery")

    return {"media_path": media_path, "media_type": media_type}