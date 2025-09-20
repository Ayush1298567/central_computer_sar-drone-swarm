import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  PlayIcon,
  PauseIcon,
  StopIcon,
  SpeakerWaveIcon,
  SpeakerXMarkIcon,
  ArrowsPointingOutIcon,
  ArrowsPointingInIcon,
  PhotoIcon,
  VideoCameraIcon,
  Cog6ToothIcon,
  ExclamationTriangleIcon,
  SignalIcon,
  WifiIcon
} from '@heroicons/react/24/outline';
import { Drone, VideoFeedConfig } from '../../types';
import { useWebSocket } from '../../hooks/useWebSocket';

interface VideoFeedProps {
  drone: Drone;
  config?: VideoFeedConfig;
  onConfigChange?: (config: VideoFeedConfig) => void;
  autoplay?: boolean;
  controls?: boolean;
  className?: string;
}

interface VideoStats {
  fps: number;
  bitrate: number;
  resolution: string;
  latency: number;
  packetsLost: number;
  connectionQuality: 'excellent' | 'good' | 'fair' | 'poor';
}

const VideoFeed: React.FC<VideoFeedProps> = ({
  drone,
  config,
  onConfigChange,
  autoplay = true,
  controls = true,
  className = ''
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const webSocket = useWebSocket();
  
  const [isPlaying, setIsPlaying] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [videoStats, setVideoStats] = useState<VideoStats>({
    fps: 0,
    bitrate: 0,
    resolution: '0x0',
    latency: 0,
    packetsLost: 0,
    connectionQuality: 'poor'
  });
  const [showSettings, setShowSettings] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [streamUrl, setStreamUrl] = useState<string | null>(null);

  const defaultConfig: VideoFeedConfig = {
    droneId: drone.id,
    quality: 'medium',
    fps: 30,
    recordingEnabled: false,
    ...config
  };

  const [currentConfig, setCurrentConfig] = useState<VideoFeedConfig>(defaultConfig);

  // Initialize video stream
  useEffect(() => {
    if (drone.isConnected && autoplay) {
      initializeStream();
    }
    
    return () => {
      disconnectStream();
    };
  }, [drone.isConnected, autoplay, drone.id]);

  // WebSocket event handlers
  useEffect(() => {
    webSocket.subscribe('drone_video_stream', (data) => {
      if (data.drone_id === drone.id) {
        handleVideoStreamData(data);
      }
    });

    webSocket.subscribe('drone_video_stats', (data) => {
      if (data.drone_id === drone.id) {
        setVideoStats(data.stats);
      }
    });

    webSocket.subscribe('drone_disconnected', (data) => {
      if (data.drone_id === drone.id) {
        setError('Drone disconnected');
        setIsPlaying(false);
        setStreamUrl(null);
      }
    });

    return () => {
      webSocket.unsubscribe('drone_video_stream');
      webSocket.unsubscribe('drone_video_stats');
      webSocket.unsubscribe('drone_disconnected');
    };
  }, [webSocket, drone.id]);

  // Initialize video stream
  const initializeStream = useCallback(async () => {
    if (!drone.isConnected) {
      setError('Drone is not connected');
      return;
    }

    setIsConnecting(true);
    setError(null);

    try {
      // Request video stream from drone
      webSocket.emit('drone_command', {
        droneId: drone.id,
        command: {
          action: 'start_video_stream',
          config: currentConfig
        }
      });

      // Simulate stream URL (in real implementation, this would come from the drone)
      const simulatedStreamUrl = `ws://localhost:8000/video/drone/${drone.id}`;
      setStreamUrl(simulatedStreamUrl);
      
      setTimeout(() => {
        setIsConnecting(false);
        setIsPlaying(true);
      }, 2000);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to initialize video stream');
      setIsConnecting(false);
    }
  }, [drone.isConnected, drone.id, currentConfig, webSocket]);

  // Disconnect video stream
  const disconnectStream = useCallback(() => {
    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.src = '';
    }
    
    webSocket.emit('drone_command', {
      droneId: drone.id,
      command: { action: 'stop_video_stream' }
    });

    setIsPlaying(false);
    setStreamUrl(null);
  }, [drone.id, webSocket]);

  // Handle video stream data
  const handleVideoStreamData = useCallback((data: any) => {
    if (videoRef.current && data.stream_url) {
      videoRef.current.src = data.stream_url;
      setStreamUrl(data.stream_url);
      
      if (autoplay && !isPlaying) {
        videoRef.current.play().catch(console.error);
        setIsPlaying(true);
      }
    }
  }, [autoplay, isPlaying]);

  // Play/pause video
  const togglePlayback = useCallback(() => {
    if (!videoRef.current) return;

    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      videoRef.current.play().catch(console.error);
      setIsPlaying(true);
    }
  }, [isPlaying]);

  // Toggle fullscreen
  const toggleFullscreen = useCallback(() => {
    if (!videoRef.current) return;

    if (isFullscreen) {
      document.exitFullscreen().catch(console.error);
    } else {
      videoRef.current.requestFullscreen().catch(console.error);
    }
  }, [isFullscreen]);

  // Toggle mute
  const toggleMute = useCallback(() => {
    if (!videoRef.current) return;

    videoRef.current.muted = !isMuted;
    setIsMuted(!isMuted);
  }, [isMuted]);

  // Take screenshot
  const takeScreenshot = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const video = videoRef.current;
    const context = canvas.getContext('2d');

    if (!context) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0);

    // Download screenshot
    canvas.toBlob((blob) => {
      if (blob) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `drone-${drone.id}-screenshot-${Date.now()}.png`;
        a.click();
        URL.revokeObjectURL(url);
      }
    }, 'image/png');
  }, [drone.id]);

  // Start/stop recording
  const toggleRecording = useCallback(() => {
    const newRecordingState = !isRecording;
    
    webSocket.emit('drone_command', {
      droneId: drone.id,
      command: {
        action: newRecordingState ? 'start_recording' : 'stop_recording',
        config: currentConfig
      }
    });

    setIsRecording(newRecordingState);
  }, [isRecording, drone.id, currentConfig, webSocket]);

  // Update configuration
  const updateConfig = useCallback((updates: Partial<VideoFeedConfig>) => {
    const newConfig = { ...currentConfig, ...updates };
    setCurrentConfig(newConfig);
    
    if (onConfigChange) {
      onConfigChange(newConfig);
    }

    // Apply configuration to stream
    if (isPlaying) {
      webSocket.emit('drone_command', {
        droneId: drone.id,
        command: {
          action: 'update_video_config',
          config: newConfig
        }
      });
    }
  }, [currentConfig, onConfigChange, isPlaying, drone.id, webSocket]);

  // Handle fullscreen change
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  // Get connection quality color
  const getQualityColor = (quality: string) => {
    switch (quality) {
      case 'excellent': return 'text-green-600';
      case 'good': return 'text-blue-600';
      case 'fair': return 'text-yellow-600';
      case 'poor': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  // Render video controls
  const renderControls = () => {
    if (!controls) return null;

    return (
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <button
              onClick={togglePlayback}
              disabled={!streamUrl}
              className="p-2 bg-white/20 rounded-full hover:bg-white/30 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isPlaying ? (
                <PauseIcon className="w-5 h-5 text-white" />
              ) : (
                <PlayIcon className="w-5 h-5 text-white" />
              )}
            </button>

            <button
              onClick={toggleMute}
              disabled={!streamUrl}
              className="p-2 bg-white/20 rounded-full hover:bg-white/30 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isMuted ? (
                <SpeakerXMarkIcon className="w-5 h-5 text-white" />
              ) : (
                <SpeakerWaveIcon className="w-5 h-5 text-white" />
              )}
            </button>

            <button
              onClick={takeScreenshot}
              disabled={!isPlaying}
              className="p-2 bg-white/20 rounded-full hover:bg-white/30 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <PhotoIcon className="w-5 h-5 text-white" />
            </button>

            <button
              onClick={toggleRecording}
              disabled={!isPlaying}
              className={`p-2 rounded-full hover:bg-white/30 disabled:opacity-50 disabled:cursor-not-allowed ${
                isRecording ? 'bg-red-500' : 'bg-white/20'
              }`}
            >
              <VideoCameraIcon className="w-5 h-5 text-white" />
            </button>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 bg-white/20 rounded-full hover:bg-white/30"
            >
              <Cog6ToothIcon className="w-5 h-5 text-white" />
            </button>

            <button
              onClick={toggleFullscreen}
              className="p-2 bg-white/20 rounded-full hover:bg-white/30"
            >
              {isFullscreen ? (
                <ArrowsPointingInIcon className="w-5 h-5 text-white" />
              ) : (
                <ArrowsPointingOutIcon className="w-5 h-5 text-white" />
              )}
            </button>
          </div>
        </div>

        {/* Settings panel */}
        {showSettings && (
          <div className="mt-4 p-3 bg-black/60 rounded-lg">
            <div className="grid grid-cols-2 gap-4 text-white">
              <div>
                <label className="block text-sm font-medium mb-1">Quality</label>
                <select
                  value={currentConfig.quality}
                  onChange={(e) => updateConfig({ quality: e.target.value as any })}
                  className="w-full bg-white/20 border border-white/30 rounded px-2 py-1 text-white"
                >
                  <option value="low">Low (480p)</option>
                  <option value="medium">Medium (720p)</option>
                  <option value="high">High (1080p)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Frame Rate</label>
                <select
                  value={currentConfig.fps}
                  onChange={(e) => updateConfig({ fps: parseInt(e.target.value) })}
                  className="w-full bg-white/20 border border-white/30 rounded px-2 py-1 text-white"
                >
                  <option value="15">15 FPS</option>
                  <option value="30">30 FPS</option>
                  <option value="60">60 FPS</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  // Render status overlay
  const renderStatusOverlay = () => (
    <div className="absolute top-4 left-4 right-4 flex justify-between items-start">
      <div className="bg-black/60 rounded-lg p-3 text-white">
        <div className="flex items-center space-x-2 mb-2">
          <div className={`w-3 h-3 rounded-full ${
            drone.isConnected ? 'bg-green-500' : 'bg-red-500'
          }`} />
          <span className="text-sm font-medium">{drone.name}</span>
        </div>
        
        <div className="space-y-1 text-xs">
          <div>Resolution: {videoStats.resolution}</div>
          <div>FPS: {videoStats.fps}</div>
          <div>Latency: {videoStats.latency}ms</div>
        </div>
      </div>

      <div className="bg-black/60 rounded-lg p-3 text-white">
        <div className="flex items-center space-x-2 mb-2">
          <SignalIcon className={`w-4 h-4 ${getQualityColor(videoStats.connectionQuality)}`} />
          <span className={`text-sm font-medium ${getQualityColor(videoStats.connectionQuality)}`}>
            {videoStats.connectionQuality}
          </span>
        </div>
        
        <div className="space-y-1 text-xs">
          <div>Bitrate: {(videoStats.bitrate / 1000).toFixed(1)} Mbps</div>
          <div>Lost: {videoStats.packetsLost} packets</div>
        </div>
      </div>
    </div>
  );

  return (
    <div className={`relative bg-black rounded-lg overflow-hidden ${className}`}>
      {/* Video element */}
      <video
        ref={videoRef}
        className="w-full h-full object-cover"
        autoPlay={autoplay}
        muted={isMuted}
        playsInline
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onError={() => setError('Video playback error')}
      />

      {/* Hidden canvas for screenshots */}
      <canvas ref={canvasRef} className="hidden" />

      {/* Loading/Error states */}
      {isConnecting && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/80">
          <div className="text-center text-white">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-2"></div>
            <div>Connecting to video stream...</div>
          </div>
        </div>
      )}

      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/80">
          <div className="text-center text-white">
            <ExclamationTriangleIcon className="w-12 h-12 mx-auto mb-2 text-red-500" />
            <div className="text-lg font-medium mb-2">Video Stream Error</div>
            <div className="text-sm text-gray-300 mb-4">{error}</div>
            <button
              onClick={initializeStream}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              Retry Connection
            </button>
          </div>
        </div>
      )}

      {!streamUrl && !isConnecting && !error && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/80">
          <div className="text-center text-white">
            <WifiIcon className="w-12 h-12 mx-auto mb-2 text-gray-400" />
            <div className="text-lg font-medium mb-2">No Video Stream</div>
            <div className="text-sm text-gray-300 mb-4">
              {drone.isConnected ? 'Click to start video stream' : 'Drone is not connected'}
            </div>
            {drone.isConnected && (
              <button
                onClick={initializeStream}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
              >
                Start Stream
              </button>
            )}
          </div>
        </div>
      )}

      {/* Status overlay */}
      {isPlaying && renderStatusOverlay()}

      {/* Controls */}
      {renderControls()}

      {/* Recording indicator */}
      {isRecording && (
        <div className="absolute top-4 right-4 flex items-center space-x-2 bg-red-500 text-white px-3 py-1 rounded-full">
          <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
          <span className="text-sm font-medium">REC</span>
        </div>
      )}
    </div>
  );
};

export default VideoFeed;