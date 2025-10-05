"""
Video Streaming Service for SAR Mission Commander
Provides real-time video streaming capabilities for multiple drones
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field

from ..core.database import SessionLocal
from ..models.drone import Drone
from ..utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class VideoStream:
    """Represents a video stream from a drone"""
    drone_id: str
    stream_id: str
    url: str
    status: str = "inactive"  # inactive, active, error
    metadata: Dict[str, Any] = field(default_factory=dict)
    connected_clients: int = 0
    last_frame: Optional[datetime] = None

class VideoStreamingService:
    """Manages video streaming for multiple drones"""

    def __init__(self):
        self.active_streams: Dict[str, VideoStream] = {}
        self._running = False

    async def start(self):
        """Start the video streaming service"""
        self._running = True
        logger.info("Video Streaming service started")

        # Start background monitoring
        asyncio.create_task(self._monitor_streams())

    async def stop(self):
        """Stop the video streaming service"""
        self._running = False
        logger.info("Video Streaming service stopped")

    async def start_stream(self, drone_id: str, stream_url: str = None) -> Optional[str]:
        """Start video streaming for a drone"""
        try:
            if drone_id in self.active_streams:
                logger.warning(f"Stream already active for drone {drone_id}")
                return self.active_streams[drone_id].stream_id

            # Generate stream ID
            stream_id = f"stream_{drone_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

            # Create stream object
            stream = VideoStream(
                drone_id=drone_id,
                stream_id=stream_id,
                url=stream_url or f"ws://localhost:8000/video/{drone_id}",
                status="active",
                metadata={
                    "resolution": "1920x1080",
                    "fps": 30,
                    "bitrate": "5Mbps",
                    "codec": "H.264"
                }
            )

            self.active_streams[drone_id] = stream
            logger.info(f"Started video stream for drone {drone_id}: {stream_id}")

            return stream_id

        except Exception as e:
            logger.error(f"Failed to start stream for drone {drone_id}: {e}")
            return None

    async def stop_stream(self, drone_id: str) -> bool:
        """Stop video streaming for a drone"""
        try:
            if drone_id not in self.active_streams:
                logger.warning(f"No active stream found for drone {drone_id}")
                return False

            stream = self.active_streams[drone_id]
            stream.status = "inactive"
            stream.connected_clients = 0

            # Remove from active streams after a delay
            asyncio.create_task(self._cleanup_stream(drone_id))

            logger.info(f"Stopped video stream for drone {drone_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to stop stream for drone {drone_id}: {e}")
            return False

    async def _cleanup_stream(self, drone_id: str, delay: int = 30):
        """Clean up a stream after delay"""
        await asyncio.sleep(delay)

        if drone_id in self.active_streams:
            del self.active_streams[drone_id]
            logger.info(f"Cleaned up stream for drone {drone_id}")

    async def get_stream_info(self, drone_id: str) -> Optional[VideoStream]:
        """Get stream information for a drone"""
        return self.active_streams.get(drone_id)

    async def get_all_streams(self) -> List[VideoStream]:
        """Get all active video streams"""
        return list(self.active_streams.values())

    async def update_stream_metadata(self, drone_id: str, metadata: Dict[str, Any]) -> bool:
        """Update stream metadata"""
        try:
            if drone_id in self.active_streams:
                self.active_streams[drone_id].metadata.update(metadata)
                self.active_streams[drone_id].last_frame = datetime.utcnow()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update metadata for drone {drone_id}: {e}")
            return False

    async def _monitor_streams(self):
        """Background task to monitor stream health"""
        while self._running:
            try:
                await asyncio.sleep(60)  # Check every minute

                for drone_id, stream in list(self.active_streams.items()):
                    # Check if stream is stale (no updates for 5 minutes)
                    if stream.last_frame and (datetime.utcnow() - stream.last_frame).seconds > 300:
                        logger.warning(f"Stream for drone {drone_id} appears stale")
                        stream.status = "error"

                        # Auto-restart stream if possible
                        await self._restart_stream(drone_id)

            except Exception as e:
                logger.error(f"Error monitoring streams: {e}")
                await asyncio.sleep(60)

    async def _restart_stream(self, drone_id: str) -> bool:
        """Attempt to restart a failed stream"""
        try:
            logger.info(f"Attempting to restart stream for drone {drone_id}")

            # Stop current stream
            await self.stop_stream(drone_id)

            # Start new stream
            return await self.start_stream(drone_id) is not None

        except Exception as e:
            logger.error(f"Failed to restart stream for drone {drone_id}: {e}")
            return False

    def get_stream_url(self, drone_id: str) -> Optional[str]:
        """Get WebSocket URL for drone video stream"""
        if drone_id in self.active_streams:
            return self.active_streams[drone_id].url
        return None

    def is_stream_active(self, drone_id: str) -> bool:
        """Check if drone has an active video stream"""
        return drone_id in self.active_streams and self.active_streams[drone_id].status == "active"

# Global video streaming service instance
video_streaming_service = VideoStreamingService()
