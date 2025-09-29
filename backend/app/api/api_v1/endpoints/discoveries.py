"""
Discovery API endpoints.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging
import uuid
import os
from datetime import datetime

from app.core.database import get_db
from app.models import Discovery, EvidenceFile, Mission
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[Dict[str, Any]])
async def get_discoveries(
    skip: int = 0,
    limit: int = 100,
    mission_id: str = None,
    status_filter: str = None,
    priority_filter: str = None,
    discovery_type: str = None,
    db: Session = Depends(get_db)
):
    """Get all discoveries with optional filtering."""
    try:
        query = db.query(Discovery)

        if mission_id:
            mission = db.query(Mission).filter(Mission.mission_id == mission_id).first()
            if mission:
                query = query.filter(Discovery.mission_id == mission.id)

        if status_filter:
            query = query.filter(Discovery.status == status_filter)

        if priority_filter:
            query = query.filter(Discovery.priority == priority_filter)

        if discovery_type:
            query = query.filter(Discovery.discovery_type == discovery_type)

        discoveries = query.order_by(Discovery.detected_at.desc()).offset(skip).limit(limit).all()

        return [
            {
                "id": discovery.id,
                "discovery_id": discovery.discovery_id,
                "mission_id": discovery.mission_id,
                "location": {
                    "lat": discovery.latitude,
                    "lng": discovery.longitude,
                    "alt": discovery.altitude
                },
                "accuracy": discovery.accuracy,
                "discovery_type": discovery.discovery_type,
                "confidence": discovery.confidence,
                "detection_method": discovery.detection_method,
                "detected_by_drone": discovery.detected_by_drone,
                "status": discovery.status,
                "priority": discovery.priority,
                "requires_investigation": discovery.requires_investigation,
                "investigation_radius": discovery.investigation_radius,
                "assigned_drone_id": discovery.assigned_drone_id,
                "investigated_at": discovery.investigated_at.isoformat() if discovery.investigated_at else None,
                "investigation_notes": discovery.investigation_notes,
                "metadata": discovery.metadata,
                "image_urls": discovery.image_urls,
                "video_url": discovery.video_url,
                "detected_at": discovery.detected_at.isoformat(),
                "confirmed_at": discovery.confirmed_at.isoformat() if discovery.confirmed_at else None,
                "updated_at": discovery.updated_at.isoformat()
            }
            for discovery in discoveries
        ]
    except Exception as e:
        logger.error(f"Error fetching discoveries: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{discovery_id}", response_model=Dict[str, Any])
async def get_discovery(
    discovery_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific discovery by ID."""
    try:
        discovery = db.query(Discovery).filter(Discovery.discovery_id == discovery_id).first()
        if not discovery:
            raise HTTPException(status_code=404, detail="Discovery not found")

        # Get associated evidence files
        evidence_files = db.query(EvidenceFile).filter(EvidenceFile.discovery_id == discovery.id).all()

        return {
            "id": discovery.id,
            "discovery_id": discovery.discovery_id,
            "mission_id": discovery.mission_id,
            "location": {
                "lat": discovery.latitude,
                "lng": discovery.longitude,
                "alt": discovery.altitude
            },
            "accuracy": discovery.accuracy,
            "discovery_type": discovery.discovery_type,
            "confidence": discovery.confidence,
            "detection_method": discovery.detection_method,
            "detected_by_drone": discovery.detected_by_drone,
            "status": discovery.status,
            "priority": discovery.priority,
            "requires_investigation": discovery.requires_investigation,
            "investigation_radius": discovery.investigation_radius,
            "assigned_drone_id": discovery.assigned_drone_id,
            "investigated_at": discovery.investigated_at.isoformat() if discovery.investigated_at else None,
            "investigation_notes": discovery.investigation_notes,
            "metadata": discovery.metadata,
            "image_urls": discovery.image_urls,
            "video_url": discovery.video_url,
            "evidence_files": [
                {
                    "id": ef.id,
                    "file_name": ef.file_name,
                    "file_type": ef.file_type,
                    "file_size": ef.file_size,
                    "uploaded_at": ef.uploaded_at.isoformat(),
                    "description": ef.description,
                    "is_primary": ef.is_primary
                }
                for ef in evidence_files
            ],
            "detected_at": discovery.detected_at.isoformat(),
            "confirmed_at": discovery.confirmed_at.isoformat() if discovery.confirmed_at else None,
            "updated_at": discovery.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching discovery {discovery_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/")
async def create_discovery(
    discovery_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Create a new discovery."""
    try:
        # Verify mission exists
        mission = db.query(Mission).filter(Mission.mission_id == discovery_data["mission_id"]).first()
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")

        # Generate unique discovery ID
        discovery_id = f"discovery_{uuid.uuid4().hex[:8]}"

        # Create new discovery
        discovery = Discovery(
            discovery_id=discovery_id,
            mission_id=mission.id,
            latitude=discovery_data["location"]["lat"],
            longitude=discovery_data["location"]["lng"],
            altitude=discovery_data["location"].get("alt"),
            accuracy=discovery_data.get("accuracy"),
            discovery_type=discovery_data["discovery_type"],
            confidence=discovery_data["confidence"],
            detection_method=discovery_data.get("detection_method", "AI"),
            detected_by_drone=discovery_data.get("detected_by_drone"),
            status=discovery_data.get("status", "detected"),
            priority=discovery_data.get("priority", "medium"),
            requires_investigation=discovery_data.get("requires_investigation", True),
            investigation_radius=discovery_data.get("investigation_radius", 100.0),
            assigned_drone_id=discovery_data.get("assigned_drone_id"),
            metadata=discovery_data.get("metadata"),
            image_urls=discovery_data.get("image_urls"),
            video_url=discovery_data.get("video_url")
        )

        db.add(discovery)
        db.commit()
        db.refresh(discovery)

        # Update mission discovery count
        mission.discoveries_count += 1
        db.commit()

        logger.info(f"Created new discovery {discovery_id}")
        return {
            "message": "Discovery created successfully",
            "discovery_id": discovery_id,
            "id": discovery.id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating discovery: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{discovery_id}/update")
async def update_discovery(
    discovery_id: str,
    updates: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update discovery information."""
    try:
        discovery = db.query(Discovery).filter(Discovery.discovery_id == discovery_id).first()
        if not discovery:
            raise HTTPException(status_code=404, detail="Discovery not found")

        # Update discovery fields
        for key, value in updates.items():
            if hasattr(discovery, key):
                setattr(discovery, key, value)

        discovery.updated_at = func.now()
        db.commit()

        logger.info(f"Updated discovery {discovery_id}")
        return {"message": "Discovery updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating discovery {discovery_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{discovery_id}/evidence")
async def upload_evidence(
    discovery_id: str,
    file: UploadFile = File(...),
    description: str = None,
    is_primary: bool = False,
    db: Session = Depends(get_db)
):
    """Upload evidence file for a discovery."""
    try:
        discovery = db.query(Discovery).filter(Discovery.discovery_id == discovery_id).first()
        if not discovery:
            raise HTTPException(status_code=404, detail="Discovery not found")

        # Ensure upload directory exists
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Create evidence record
        evidence = EvidenceFile(
            discovery_id=discovery.id,
            file_name=file.filename,
            file_path=file_path,
            file_type=file.content_type or "application/octet-stream",
            file_size=len(content),
            description=description,
            is_primary=is_primary,
            metadata={"original_filename": file.filename}
        )

        db.add(evidence)
        db.commit()

        # Update discovery image/video URLs
        if file.content_type and file.content_type.startswith("image/"):
            if not discovery.image_urls:
                discovery.image_urls = []
            discovery.image_urls.append(f"/uploads/{unique_filename}")
        elif file.content_type and file.content_type.startswith("video/"):
            discovery.video_url = f"/uploads/{unique_filename}"

        db.commit()

        logger.info(f"Uploaded evidence file for discovery {discovery_id}")
        return {
            "message": "Evidence file uploaded successfully",
            "file_id": evidence.id,
            "file_path": file_path
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading evidence for discovery {discovery_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{discovery_id}/investigate")
async def start_investigation(
    discovery_id: str,
    drone_id: str,
    db: Session = Depends(get_db)
):
    """Start investigation of a discovery."""
    try:
        discovery = db.query(Discovery).filter(Discovery.discovery_id == discovery_id).first()
        if not discovery:
            raise HTTPException(status_code=404, detail="Discovery not found")

        # Update discovery status
        discovery.status = "investigating"
        discovery.assigned_drone_id = drone_id
        discovery.investigated_at = datetime.utcnow()
        db.commit()

        logger.info(f"Started investigation of discovery {discovery_id} with drone {drone_id}")
        return {"message": "Investigation started successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting investigation for discovery {discovery_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{discovery_id}/complete-investigation")
async def complete_investigation(
    discovery_id: str,
    result: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Complete investigation of a discovery."""
    try:
        discovery = db.query(Discovery).filter(Discovery.discovery_id == discovery_id).first()
        if not discovery:
            raise HTTPException(status_code=404, detail="Discovery not found")

        # Update discovery status
        discovery.status = "investigated"
        discovery.investigation_notes = result.get("notes")
        discovery.metadata = {**(discovery.metadata or {}), **result.get("metadata", {})}

        # Update assigned drone
        if discovery.assigned_drone_id:
            discovery.assigned_drone_id = None

        db.commit()

        logger.info(f"Completed investigation of discovery {discovery_id}")
        return {"message": "Investigation completed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing investigation for discovery {discovery_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")