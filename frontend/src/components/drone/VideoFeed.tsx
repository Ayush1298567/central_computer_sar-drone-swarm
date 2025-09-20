import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  Pause, 
  Square, 
  Volume2, 
  VolumeX, 
  Maximize, 
  Minimize,
  Camera,
  Video,
  Settings,
  AlertCircle,
  Loader,
  Eye,
  EyeOff
} from 'lucide-react';
import { Drone, VideoFeedData } from '../../types/drone';
import { webSocketService } from '../../services/websocket';

interface VideoFeedProps {
  drone: Drone;
  onRecordingStart?: (drone: Drone) => void;
  onRecordingStop?: (drone: Drone) => void;
  onScreenshot?: (drone: Drone) => void;
  className?: string;
}

interface VideoSettings {
  quality: 'low' | 'medium' | 'high';
  nightVision: boolean;
  thermalOverlay: boolean;
  stabilization: boolean;
}

export const VideoFeed: React.FC<VideoFeedProps> = ({
  drone,
  onRecordingStart,
  onRecordingStop,
  onScreenshot,
  className = '',
}) => {
  const [feedData, setFeedData] = useState<VideoFeedData | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState<VideoSettings>({
    quality: 'medium',
    nightVision: false,
    thermalOverlay: false,
    stabilization: true,
  });

  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Initialize video feed
  useEffect(() => {
    if (drone.status === 'offline' || drone.status === 'error') {
      setError('Drone is offline or in error state');
      setIsLoading(false);
      return;
    }

    // Simulate video feed data (in real app, this would come from API)
    const mockFeedData: VideoFeedData = {
      drone_id: drone.id,
      stream_url: `ws://localhost:8000/video/${drone.id}`,
      quality: settings.quality,
      is_recording: false,
      timestamp: new Date().toISOString(),
    };

    setFeedData(mockFeedData);
    setIsLoading(false);
  }, [drone.id, drone.status, settings.quality]);

  // Subscribe to video feed updates
  useEffect(() => {
    if (!feedData) return;

    const handleVideoUpdate = (data: any) => {
      if (data.drone_id === drone.id) {
        setFeedData(prev => prev ? { ...prev, ...data } : data);
        setIsRecording(data.is_recording || false);
      }
    };

    webSocketService.subscribe('video_feed_update', handleVideoUpdate);

    return () => {
      webSocketService.unsubscribe('video_feed_update', handleVideoUpdate);
    };
  }, [drone.id, feedData]);

  // Handle fullscreen changes
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const handlePlayPause = () => {
    if (!videoRef.current) return;

    if (isPlaying) {
      videoRef.current.pause();
    } else {
      videoRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleMuteToggle = () => {
    if (!videoRef.current) return;
    
    videoRef.current.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const handleFullscreenToggle = () => {
    if (!containerRef.current) return;

    if (isFullscreen) {
      document.exitFullscreen();
    } else {
      containerRef.current.requestFullscreen();
    }
  };

  const handleRecordingToggle = () => {
    if (isRecording) {
      onRecordingStop?.(drone);
    } else {
      onRecordingStart?.(drone);
    }
  };

  const handleScreenshot = () => {
    onScreenshot?.(drone);
  };

  const handleSettingsChange = (key: keyof VideoSettings, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  const getQualityColor = (quality: string) => {
    switch (quality) {
      case 'high': return 'text-green-600';
      case 'medium': return 'text-yellow-600';
      case 'low': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  if (error) {
    return (
      <div className={`bg-black rounded-lg overflow-hidden relative ${className}`}>
        <div className="aspect-video flex items-center justify-center">
          <div className="text-center text-white">
            <AlertCircle size={48} className="mx-auto mb-4 text-red-500" />
            <p className="text-lg font-medium mb-2">Video Feed Unavailable</p>
            <p className="text-sm text-gray-400">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (isLoading || !feedData) {
    return (
      <div className={`bg-black rounded-lg overflow-hidden relative ${className}`}>
        <div className="aspect-video flex items-center justify-center">
          <div className="text-center text-white">
            <Loader size={48} className="mx-auto mb-4 animate-spin" />
            <p className="text-lg font-medium">Connecting to video feed...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div 
      ref={containerRef}
      className={`bg-black rounded-lg overflow-hidden relative group ${className} ${
        isFullscreen ? 'fixed inset-0 z-50 rounded-none' : ''
      }`}
    >
      {/* Video Element */}
      <video
        ref={videoRef}
        className="w-full h-full object-cover"
        muted={isMuted}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onError={() => setError('Failed to load video stream')}
      >
        <source src={feedData.stream_url} type="video/webm" />
        Your browser does not support the video tag.
      </video>

      {/* Overlay Controls */}
      <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all duration-200">
        {/* Top Bar */}
        <div className="absolute top-0 left-0 right-0 bg-gradient-to-b from-black via-transparent to-transparent p-4 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <div className="flex items-center justify-between text-white">
            <div className="flex items-center space-x-4">
              <h3 className="font-medium">{drone.name} - Live Feed</h3>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                <span className="text-sm">LIVE</span>
              </div>
              <span className={`text-sm font-medium ${getQualityColor(feedData.quality)}`}>
                {feedData.quality.toUpperCase()}
              </span>
            </div>
            
            <div className="flex items-center space-x-2">
              {/* Settings */}
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
              >
                <Settings size={20} />
              </button>
              
              {/* Fullscreen */}
              <button
                onClick={handleFullscreenToggle}
                className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
              >
                {isFullscreen ? <Minimize size={20} /> : <Maximize size={20} />}
              </button>
            </div>
          </div>
        </div>

        {/* Center Play Button */}
        {!isPlaying && (
          <div className="absolute inset-0 flex items-center justify-center">
            <button
              onClick={handlePlayPause}
              className="w-20 h-20 bg-white bg-opacity-20 hover:bg-opacity-30 rounded-full flex items-center justify-center transition-all duration-200"
            >
              <Play size={32} className="text-white ml-1" />
            </button>
          </div>
        )}

        {/* Bottom Controls */}
        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black via-transparent to-transparent p-4 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <div className="flex items-center justify-between text-white">
            <div className="flex items-center space-x-4">
              {/* Play/Pause */}
              <button
                onClick={handlePlayPause}
                className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
              >
                {isPlaying ? <Pause size={20} /> : <Play size={20} />}
              </button>

              {/* Mute */}
              <button
                onClick={handleMuteToggle}
                className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
              >
                {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
              </button>

              {/* Quality Indicator */}
              <div className="text-sm">
                {feedData.quality} • {drone.capabilities.camera_resolution}
              </div>
            </div>

            <div className="flex items-center space-x-2">
              {/* Screenshot */}
              <button
                onClick={handleScreenshot}
                className="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
                title="Take Screenshot"
              >
                <Camera size={20} />
              </button>

              {/* Recording */}
              <button
                onClick={handleRecordingToggle}
                className={`p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition-colors ${
                  isRecording ? 'bg-red-600' : ''
                }`}
                title={isRecording ? 'Stop Recording' : 'Start Recording'}
              >
                {isRecording ? <Square size={20} /> : <Video size={20} />}
              </button>
            </div>
          </div>
        </div>

        {/* Recording Indicator */}
        {isRecording && (
          <div className="absolute top-4 right-4 flex items-center space-x-2 bg-red-600 px-3 py-1 rounded-full text-white text-sm">
            <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
            <span>REC</span>
          </div>
        )}
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="absolute top-16 right-4 bg-white rounded-lg shadow-lg p-4 z-10 min-w-64">
          <h4 className="font-medium text-gray-900 mb-4">Video Settings</h4>
          
          <div className="space-y-4">
            {/* Quality */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Quality
              </label>
              <select
                value={settings.quality}
                onChange={(e) => handleSettingsChange('quality', e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="low">Low (480p)</option>
                <option value="medium">Medium (720p)</option>
                <option value="high">High (1080p)</option>
              </select>
            </div>

            {/* Night Vision */}
            {drone.capabilities.night_vision && (
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-gray-700">
                  Night Vision
                </label>
                <button
                  onClick={() => handleSettingsChange('nightVision', !settings.nightVision)}
                  className={`p-1 rounded ${
                    settings.nightVision ? 'text-blue-600' : 'text-gray-400'
                  }`}
                >
                  {settings.nightVision ? <Eye size={20} /> : <EyeOff size={20} />}
                </button>
              </div>
            )}

            {/* Thermal Overlay */}
            {drone.capabilities.thermal_camera && (
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-gray-700">
                  Thermal Overlay
                </label>
                <input
                  type="checkbox"
                  checked={settings.thermalOverlay}
                  onChange={(e) => handleSettingsChange('thermalOverlay', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </div>
            )}

            {/* Stabilization */}
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Stabilization
              </label>
              <input
                type="checkbox"
                checked={settings.stabilization}
                onChange={(e) => handleSettingsChange('stabilization', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
            </div>
          </div>

          <button
            onClick={() => setShowSettings(false)}
            className="w-full mt-4 btn btn-secondary text-sm"
          >
            Close
          </button>
        </div>
      )}
    </div>
  );
};