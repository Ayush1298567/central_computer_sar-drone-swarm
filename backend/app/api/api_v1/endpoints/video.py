"""
Video streaming endpoints for SAR Mission Commander
Provides WebSocket endpoints for real-time video streaming
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from app.core.database import get_db

from app.services.video_streaming import video_streaming_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Active WebSocket connections for video streams
active_video_connections: Dict[str, List[WebSocket]] = {}

@router.websocket("/{drone_id}")
async def video_stream_websocket(websocket: WebSocket, drone_id: str):
    """WebSocket endpoint for real-time video streaming from a drone"""
    await websocket.accept()

    try:
        # Add connection to active connections
        if drone_id not in active_video_connections:
            active_video_connections[drone_id] = []

        active_video_connections[drone_id].append(websocket)
        video_streaming_service.active_streams[drone_id].connected_clients += 1

        logger.info(f"Video WebSocket connected for drone {drone_id}. Total clients: {len(active_video_connections[drone_id])}")

        # Start video stream if not already active
        stream_id = await video_streaming_service.start_stream(drone_id)
        if stream_id:
            logger.info(f"Started video stream {stream_id} for drone {drone_id}")

        # Send initial stream info
        stream_info = await video_streaming_service.get_stream_info(drone_id)
        if stream_info:
            await websocket.send_json({
                "type": "stream_info",
                "stream_id": stream_info.stream_id,
                "status": stream_info.status,
                "metadata": stream_info.metadata,
                "timestamp": datetime.utcnow().isoformat()
            })

        # Simulate video frames (placeholder for real video streaming)
        frame_count = 0
        while True:
            try:
                # Simulate receiving a video frame
                frame_data = {
                    "type": "video_frame",
                    "drone_id": drone_id,
                    "frame_id": frame_count,
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": {
                        "resolution": "1920x1080",
                        "fps": 30,
                        "size": "150KB"
                    }
                }

                # Send frame to all connected clients
                if drone_id in active_video_connections:
                    disconnected_clients = []
                    for client in active_video_connections[drone_id]:
                        try:
                            await client.send_json(frame_data)
                        except:
                            disconnected_clients.append(client)

                    # Remove disconnected clients
                    for client in disconnected_clients:
                        active_video_connections[drone_id].remove(client)
                        if video_streaming_service.active_streams.get(drone_id):
                            video_streaming_service.active_streams[drone_id].connected_clients -= 1

                frame_count += 1

                # Update stream metadata
                await video_streaming_service.update_stream_metadata(drone_id, {
                    "last_frame": datetime.utcnow().isoformat(),
                    "total_frames": frame_count
                })

                # Simulate frame rate (30 FPS)
                await asyncio.sleep(1/30)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error sending video frame for drone {drone_id}: {e}")
                break

    except WebSocketDisconnect:
        logger.info(f"Video WebSocket disconnected for drone {drone_id}")
    except Exception as e:
        logger.error(f"Video streaming error for drone {drone_id}: {e}")
    finally:
        # Clean up connection
        if drone_id in active_video_connections:
            if websocket in active_video_connections[drone_id]:
                active_video_connections[drone_id].remove(websocket)

            # If no more connections, stop the stream
            if not active_video_connections[drone_id]:
                await video_streaming_service.stop_stream(drone_id)
                del active_video_connections[drone_id]

@router.get("/streams")
async def get_video_streams():
    """Get information about all active video streams"""
    try:
        streams = await video_streaming_service.get_all_streams()
        return {
            "streams": [
                {
                    "drone_id": stream.drone_id,
                    "stream_id": stream.stream_id,
                    "status": stream.status,
                    "connected_clients": stream.connected_clients,
                    "metadata": stream.metadata,
                    "last_frame": stream.last_frame.isoformat() if stream.last_frame else None
                }
                for stream in streams
            ],
            "total_streams": len(streams)
        }
    except Exception as e:
        logger.error(f"Error getting video streams: {e}")
        raise HTTPException(status_code=500, detail="Failed to get video streams")

@router.post("/{drone_id}/start")
async def start_video_stream(drone_id: str):
    """Start video streaming for a drone"""
    try:
        stream_id = await video_streaming_service.start_stream(drone_id)
        if stream_id:
            return {
                "success": True,
                "stream_id": stream_id,
                "message": f"Video stream started for drone {drone_id}",
                "websocket_url": f"ws://localhost:8000/api/video/{drone_id}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to start video stream")
    except Exception as e:
        logger.error(f"Error starting video stream for drone {drone_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start video stream")

@router.post("/{drone_id}/stop")
async def stop_video_stream(drone_id: str):
    """Stop video streaming for a drone"""
    try:
        success = await video_streaming_service.stop_stream(drone_id)
        if success:
            return {
                "success": True,
                "message": f"Video stream stopped for drone {drone_id}"
            }
        else:
            raise HTTPException(status_code=404, detail="No active stream found")
    except Exception as e:
        logger.error(f"Error stopping video stream for drone {drone_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop video stream")
