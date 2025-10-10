"""
Video Stream Receiver for SAR Drone Swarm
Handles real-time video processing and analysis from drone cameras.
"""

import asyncio
import logging
import cv2
import numpy as np
import base64
import json
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException
from app.ai.real_computer_vision import computer_vision_processor
from app.core.config import settings

logger = logging.getLogger(__name__)

class VideoStreamReceiver:
    """Real video stream processing with computer vision analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_streams: Dict[str, Dict[str, Any]] = {}
        self.frame_processors: Dict[str, Callable] = {}
        self.analysis_callbacks: List[Callable] = []
        self.is_running = False
        self.frame_buffer_size = 10
        self.processing_queue = asyncio.Queue()
        
    async def start(self) -> bool:
        """Start the video stream receiver"""
        try:
            self.is_running = True
            
            # Start background processing task
            asyncio.create_task(self._process_video_frames())
            
            self.logger.info("Video Stream Receiver started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start Video Stream Receiver: {e}", exc_info=True)
            return False
    
    async def stop(self) -> bool:
        """Stop the video stream receiver"""
        try:
            self.is_running = False
            
            # Close all active streams
            for stream_id in list(self.active_streams.keys()):
                await self.stop_stream(stream_id)
            
            self.logger.info("Video Stream Receiver stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping Video Stream Receiver: {e}", exc_info=True)
            return False
    
    async def start_stream(self, stream_id: str, stream_url: str, 
                          drone_id: str, stream_type: str = "rtsp") -> bool:
        """
        Start receiving video from a drone stream.
        
        Args:
            stream_id: Unique identifier for the stream
            stream_url: URL or path to the video stream
            drone_id: ID of the drone providing the stream
            stream_type: Type of stream (rtsp, http, file, etc.)
            
        Returns:
            True if stream started successfully
        """
        try:
            if stream_id in self.active_streams:
                self.logger.warning(f"Stream {stream_id} already active")
                return False
            
            # Initialize stream data
            stream_data = {
                'stream_id': stream_id,
                'stream_url': stream_url,
                'drone_id': drone_id,
                'stream_type': stream_type,
                'started_at': datetime.utcnow(),
                'frame_count': 0,
                'last_frame_time': None,
                'is_active': True,
                'frame_buffer': [],
                'analysis_results': [],
                'error_count': 0
            }
            
            # Start stream based on type
            if stream_type == "rtsp":
                success = await self._start_rtsp_stream(stream_data)
            elif stream_type == "http":
                success = await self._start_http_stream(stream_data)
            elif stream_type == "file":
                success = await self._start_file_stream(stream_data)
            else:
                self.logger.error(f"Unsupported stream type: {stream_type}")
                return False
            
            if success:
                self.active_streams[stream_id] = stream_data
                self.logger.info(f"Started video stream {stream_id} from drone {drone_id}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting stream {stream_id}: {e}", exc_info=True)
            return False
    
    async def stop_stream(self, stream_id: str) -> bool:
        """Stop a video stream"""
        try:
            if stream_id not in self.active_streams:
                return False
            
            stream_data = self.active_streams[stream_id]
            stream_data['is_active'] = False
            
            # Clean up resources
            if 'cap' in stream_data:
                stream_data['cap'].release()
            
            del self.active_streams[stream_id]
            self.logger.info(f"Stopped video stream {stream_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping stream {stream_id}: {e}", exc_info=True)
            return False
    
    async def _start_rtsp_stream(self, stream_data: Dict[str, Any]) -> bool:
        """Start RTSP stream"""
        try:
            # Open RTSP stream
            cap = cv2.VideoCapture(stream_data['stream_url'])
            
            if not cap.isOpened():
                self.logger.error(f"Failed to open RTSP stream: {stream_data['stream_url']}")
                return False
            
            # Set buffer size
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            stream_data['cap'] = cap
            
            # Start frame reading task
            asyncio.create_task(self._read_rtsp_frames(stream_data))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting RTSP stream: {e}")
            return False
    
    async def _start_http_stream(self, stream_data: Dict[str, Any]) -> bool:
        """Start HTTP stream"""
        try:
            # Open HTTP stream
            cap = cv2.VideoCapture(stream_data['stream_url'])
            
            if not cap.isOpened():
                self.logger.error(f"Failed to open HTTP stream: {stream_data['stream_url']}")
                return False
            
            stream_data['cap'] = cap
            
            # Start frame reading task
            asyncio.create_task(self._read_http_frames(stream_data))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting HTTP stream: {e}")
            return False
    
    async def _start_file_stream(self, stream_data: Dict[str, Any]) -> bool:
        """Start file stream"""
        try:
            # Open file stream
            cap = cv2.VideoCapture(stream_data['stream_url'])
            
            if not cap.isOpened():
                self.logger.error(f"Failed to open file stream: {stream_data['stream_url']}")
                return False
            
            stream_data['cap'] = cap
            
            # Start frame reading task
            asyncio.create_task(self._read_file_frames(stream_data))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting file stream: {e}")
            return False
    
    async def _read_rtsp_frames(self, stream_data: Dict[str, Any]) -> None:
        """Read frames from RTSP stream"""
        try:
            cap = stream_data['cap']
            
            while stream_data['is_active'] and cap.isOpened():
                ret, frame = cap.read()
                
                if not ret:
                    self.logger.warning(f"Failed to read frame from RTSP stream {stream_data['stream_id']}")
                    stream_data['error_count'] += 1
                    
                    if stream_data['error_count'] > 10:
                        self.logger.error(f"Too many errors, stopping stream {stream_data['stream_id']}")
                        break
                    
                    await asyncio.sleep(0.1)
                    continue
                
                # Reset error count on successful read
                stream_data['error_count'] = 0
                
                # Process frame
                await self._process_frame(stream_data, frame)
                
                # Small delay to prevent overwhelming the system
                await asyncio.sleep(0.033)  # ~30 FPS
                
        except Exception as e:
            self.logger.error(f"Error reading RTSP frames: {e}", exc_info=True)
        finally:
            if 'cap' in stream_data:
                stream_data['cap'].release()
    
    async def _read_http_frames(self, stream_data: Dict[str, Any]) -> None:
        """Read frames from HTTP stream"""
        try:
            cap = stream_data['cap']
            
            while stream_data['is_active'] and cap.isOpened():
                ret, frame = cap.read()
                
                if not ret:
                    self.logger.warning(f"Failed to read frame from HTTP stream {stream_data['stream_id']}")
                    stream_data['error_count'] += 1
                    
                    if stream_data['error_count'] > 10:
                        self.logger.error(f"Too many errors, stopping stream {stream_data['stream_id']}")
                        break
                    
                    await asyncio.sleep(0.1)
                    continue
                
                stream_data['error_count'] = 0
                await self._process_frame(stream_data, frame)
                await asyncio.sleep(0.033)
                
        except Exception as e:
            self.logger.error(f"Error reading HTTP frames: {e}", exc_info=True)
        finally:
            if 'cap' in stream_data:
                stream_data['cap'].release()
    
    async def _read_file_frames(self, stream_data: Dict[str, Any]) -> None:
        """Read frames from file stream"""
        try:
            cap = stream_data['cap']
            
            while stream_data['is_active'] and cap.isOpened():
                ret, frame = cap.read()
                
                if not ret:
                    # End of file, restart if it's a loop
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                
                await self._process_frame(stream_data, frame)
                await asyncio.sleep(0.033)
                
        except Exception as e:
            self.logger.error(f"Error reading file frames: {e}", exc_info=True)
        finally:
            if 'cap' in stream_data:
                stream_data['cap'].release()
    
    async def _process_frame(self, stream_data: Dict[str, Any], frame: np.ndarray) -> None:
        """Process a video frame"""
        try:
            # Update stream metadata
            stream_data['frame_count'] += 1
            stream_data['last_frame_time'] = datetime.utcnow()
            
            # Add frame to buffer
            frame_data = {
                'frame': frame.copy(),
                'timestamp': datetime.utcnow(),
                'frame_number': stream_data['frame_count'],
                'stream_id': stream_data['stream_id'],
                'drone_id': stream_data['drone_id']
            }
            
            # Add to buffer (limit size)
            stream_data['frame_buffer'].append(frame_data)
            if len(stream_data['frame_buffer']) > self.frame_buffer_size:
                stream_data['frame_buffer'].pop(0)
            
            # Add to processing queue
            await self.processing_queue.put(frame_data)
            
        except Exception as e:
            self.logger.error(f"Error processing frame: {e}", exc_info=True)
    
    async def _process_video_frames(self) -> None:
        """Background task to process video frames"""
        try:
            while self.is_running:
                try:
                    # Get frame from queue with timeout
                    frame_data = await asyncio.wait_for(
                        self.processing_queue.get(), 
                        timeout=1.0
                    )
                    
                    # Process frame with computer vision
                    await self._analyze_frame(frame_data)
                    
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    self.logger.error(f"Error in frame processing loop: {e}", exc_info=True)
                    await asyncio.sleep(1)
                    
        except Exception as e:
            self.logger.error(f"Frame processing task error: {e}", exc_info=True)
    
    async def _analyze_frame(self, frame_data: Dict[str, Any]) -> None:
        """Analyze a frame using computer vision"""
        try:
            frame = frame_data['frame']
            stream_id = frame_data['stream_id']
            drone_id = frame_data['drone_id']
            
            # Run computer vision analysis
            analysis_results = await computer_vision_processor.analyze_frame(
                frame,
                drone_id=drone_id,
                stream_id=stream_id,
                timestamp=frame_data['timestamp']
            )
            
            # Store results
            if stream_id in self.active_streams:
                self.active_streams[stream_id]['analysis_results'].append({
                    'timestamp': frame_data['timestamp'],
                    'frame_number': frame_data['frame_number'],
                    'results': analysis_results
                })
                
                # Keep only recent results
                if len(self.active_streams[stream_id]['analysis_results']) > 100:
                    self.active_streams[stream_id]['analysis_results'].pop(0)
            
            # Notify callbacks
            for callback in self.analysis_callbacks:
                try:
                    await callback(stream_id, drone_id, analysis_results, frame_data)
                except Exception as e:
                    self.logger.error(f"Error in analysis callback: {e}")
            
        except Exception as e:
            self.logger.error(f"Error analyzing frame: {e}", exc_info=True)
    
    def register_analysis_callback(self, callback: Callable) -> None:
        """Register a callback for analysis results"""
        self.analysis_callbacks.append(callback)
    
    async def get_stream_status(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """Get status information for a stream"""
        try:
            if stream_id not in self.active_streams:
                return None
            
            stream_data = self.active_streams[stream_id]
            
            return {
                'stream_id': stream_id,
                'drone_id': stream_data['drone_id'],
                'is_active': stream_data['is_active'],
                'started_at': stream_data['started_at'].isoformat(),
                'frame_count': stream_data['frame_count'],
                'last_frame_time': stream_data['last_frame_time'].isoformat() if stream_data['last_frame_time'] else None,
                'error_count': stream_data['error_count'],
                'buffer_size': len(stream_data['frame_buffer']),
                'analysis_count': len(stream_data['analysis_results'])
            }
            
        except Exception as e:
            self.logger.error(f"Error getting stream status: {e}")
            return None
    
    async def get_latest_frame(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest frame from a stream"""
        try:
            if stream_id not in self.active_streams:
                return None
            
            stream_data = self.active_streams[stream_id]
            
            if not stream_data['frame_buffer']:
                return None
            
            latest_frame = stream_data['frame_buffer'][-1]
            
            # Encode frame as base64 for transmission
            _, buffer = cv2.imencode('.jpg', latest_frame['frame'])
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            return {
                'stream_id': stream_id,
                'drone_id': latest_frame['drone_id'],
                'frame_number': latest_frame['frame_number'],
                'timestamp': latest_frame['timestamp'].isoformat(),
                'frame_data': frame_base64,
                'width': latest_frame['frame'].shape[1],
                'height': latest_frame['frame'].shape[0]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting latest frame: {e}")
            return None
    
    async def get_analysis_results(self, stream_id: str, 
                                 limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent analysis results for a stream"""
        try:
            if stream_id not in self.active_streams:
                return []
            
            stream_data = self.active_streams[stream_id]
            results = stream_data['analysis_results']
            
            # Return most recent results
            return results[-limit:] if results else []
            
        except Exception as e:
            self.logger.error(f"Error getting analysis results: {e}")
            return []
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        try:
            active_streams = len([s for s in self.active_streams.values() if s['is_active']])
            total_frames = sum(s['frame_count'] for s in self.active_streams.values())
            total_errors = sum(s['error_count'] for s in self.active_streams.values())
            
            return {
                'is_running': self.is_running,
                'active_streams': active_streams,
                'total_streams': len(self.active_streams),
                'total_frames_processed': total_frames,
                'total_errors': total_errors,
                'processing_queue_size': self.processing_queue.qsize(),
                'streams': list(self.active_streams.keys())
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}

# Global instance
video_stream_receiver = VideoStreamReceiver()

# Convenience functions
async def start_video_receiver() -> bool:
    """Start the global video stream receiver"""
    return await video_stream_receiver.start()

async def stop_video_receiver() -> bool:
    """Stop the global video stream receiver"""
    return await video_stream_receiver.stop()

async def start_video_stream(stream_id: str, stream_url: str, 
                           drone_id: str, stream_type: str = "rtsp") -> bool:
    """Start a video stream"""
    return await video_stream_receiver.start_stream(stream_id, stream_url, drone_id, stream_type)

async def stop_video_stream(stream_id: str) -> bool:
    """Stop a video stream"""
    return await video_stream_receiver.stop_stream(stream_id)