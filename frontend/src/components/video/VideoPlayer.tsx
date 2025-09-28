import React, { useEffect, useRef, useState } from 'react';

interface VideoPlayerProps {
  streamId: string;
  url: string;
  isSelected?: boolean;
  onStatusChange?: (status: 'loading' | 'playing' | 'error' | 'disconnected') => void;
  className?: string;
  autoPlay?: boolean;
  muted?: boolean;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({
  streamId,
  url,
  isSelected = false,
  onStatusChange,
  className = '',
  autoPlay = true,
  muted = true,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'error' | 'disconnected'>('connecting');
  const [isPlaying, setIsPlaying] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string>('');

  // Notify parent of status changes
  useEffect(() => {
    onStatusChange?.(connectionStatus as any);
  }, [connectionStatus, onStatusChange]);

  // Initialize WebSocket connection for video stream
  useEffect(() => {
    connectToStream();

    return () => {
      disconnectFromStream();
    };
  }, [url]);

  const connectToStream = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      setConnectionStatus('connecting');
      setErrorMessage('');

      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = () => {
        console.log(`Video stream connected: ${streamId}`);
        setConnectionStatus('connected');
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'video_frame') {
            // Handle video frame data
            displayVideoFrame(data.frame);
          } else if (data.type === 'stream_metadata') {
            // Handle stream metadata
            console.log('Stream metadata:', data);
          }
        } catch (error) {
          console.error('Error processing video message:', error);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error(`Video stream error for ${streamId}:`, error);
        setConnectionStatus('error');
        setErrorMessage('Failed to connect to video stream');
      };

      wsRef.current.onclose = (event) => {
        console.log(`Video stream closed for ${streamId}:`, event.code, event.reason);
        setConnectionStatus('disconnected');

        // Attempt reconnection for unexpected disconnections
        if (event.code !== 1000) {
          scheduleReconnect();
        }
      };

    } catch (error) {
      console.error(`Failed to create WebSocket for ${streamId}:`, error);
      setConnectionStatus('error');
      setErrorMessage('Failed to create video connection');
    }
  };

  const disconnectFromStream = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Component unmounting');
      wsRef.current = null;
    }
  };

  const scheduleReconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    reconnectTimeoutRef.current = setTimeout(() => {
      console.log(`Attempting to reconnect video stream: ${streamId}`);
      connectToStream();
    }, 3000);
  };

  const displayVideoFrame = (frameData: string) => {
    if (!videoRef.current) return;

    try {
      // For WebRTC/MJPEG streams, we'd use different approaches
      // For now, we'll use a placeholder approach
      if (frameData.startsWith('data:image')) {
        // Handle base64 image data
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();

        img.onload = () => {
          canvas.width = img.width;
          canvas.height = img.height;
          ctx?.drawImage(img, 0, 0);

          if (videoRef.current) {
            videoRef.current.srcObject = canvas.captureStream(30);
          }
        };

        img.src = frameData;
      }
    } catch (error) {
      console.error('Error displaying video frame:', error);
    }
  };

  const handlePlay = () => {
    if (videoRef.current) {
      videoRef.current.play().catch(error => {
        console.error('Error playing video:', error);
        setErrorMessage('Failed to play video stream');
      });
    }
  };

  const handlePause = () => {
    if (videoRef.current) {
      videoRef.current.pause();
    }
  };

  // Fallback for when WebSocket streaming isn't available
  useEffect(() => {
    if (!videoRef.current) return;

    const video = videoRef.current;

    const handleLoadedData = () => {
      setIsPlaying(true);
      setConnectionStatus('connected');
    };

    const handleError = () => {
      setConnectionStatus('error');
      setErrorMessage('Video loading failed');
    };

    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);

    video.addEventListener('loadeddata', handleLoadedData);
    video.addEventListener('error', handleError);
    video.addEventListener('play', handlePlay);
    video.addEventListener('pause', handlePause);

    return () => {
      video.removeEventListener('loadeddata', handleLoadedData);
      video.removeEventListener('error', handleError);
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('pause', handlePause);
    };
  }, []);

  return (
    <div className={`relative w-full h-full ${className}`}>
      {/* Video Element */}
      <video
        ref={videoRef}
        className="w-full h-full object-cover"
        autoPlay={autoPlay}
        muted={muted}
        playsInline
        onError={() => setConnectionStatus('error')}
      />

      {/* Loading State */}
      {connectionStatus === 'connecting' && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-75">
          <div className="text-center">
            <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-2"></div>
            <p className="text-sm text-gray-300">Connecting...</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {connectionStatus === 'error' && (
        <div className="absolute inset-0 flex items-center justify-center bg-red-900 bg-opacity-75">
          <div className="text-center">
            <div className="text-2xl mb-2">⚠️</div>
            <p className="text-sm text-red-300">{errorMessage || 'Stream Error'}</p>
            <button
              onClick={connectToStream}
              className="mt-2 px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Disconnected State */}
      {connectionStatus === 'disconnected' && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-75">
          <div className="text-center">
            <div className="text-2xl mb-2">📡</div>
            <p className="text-sm text-gray-400">Stream Disconnected</p>
            <button
              onClick={connectToStream}
              className="mt-2 px-3 py-1 bg-gray-600 hover:bg-gray-700 rounded text-sm"
            >
              Reconnect
            </button>
          </div>
        </div>
      )}

      {/* Play/Pause Overlay for Selected Stream */}
      {isSelected && connectionStatus === 'connected' && (
        <div className="absolute bottom-2 right-2 flex gap-1">
          <button
            onClick={isPlaying ? handlePause : handlePlay}
            className="p-1 bg-black bg-opacity-50 hover:bg-opacity-75 rounded"
            title={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? '⏸️' : '▶️'}
          </button>
        </div>
      )}

      {/* Stream Info */}
      <div className="absolute top-2 left-2 bg-black bg-opacity-50 px-2 py-1 rounded text-xs">
        <div>Stream: {streamId}</div>
        <div className="capitalize">{connectionStatus}</div>
      </div>
    </div>
  );
};

export default VideoPlayer;