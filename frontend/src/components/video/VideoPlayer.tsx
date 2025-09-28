/**
 * Video Player Component
 * Handles individual video stream playback
 */

import React, { useRef, useEffect, useState, useCallback } from 'react';
import { VideoStream } from '../../types';
import { VideoControls } from './VideoControls';

interface VideoPlayerProps {
  stream: VideoStream;
  autoPlay?: boolean;
  showControls?: boolean;
  className?: string;
  onPlay?: () => void;
  onPause?: () => void;
  onError?: (error: string) => void;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({
  stream,
  autoPlay = false,
  showControls = true,
  className = '',
  onPlay,
  onPause,
  onError
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [volume, setVolume] = useState(0.7);
  const [isMuted, setIsMuted] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  // Handle stream URL changes
  useEffect(() => {
    if (videoRef.current && stream.url) {
      setIsLoading(true);
      setError(null);
      videoRef.current.src = stream.url;
      videoRef.current.load();
    }
  }, [stream.url]);

  // Auto-play when stream becomes available
  useEffect(() => {
    if (autoPlay && videoRef.current && stream.status === 'connected') {
      videoRef.current.play().catch(err => {
        console.warn('Auto-play failed:', err);
      });
    }
  }, [autoPlay, stream.status]);

  const handleLoadedData = useCallback(() => {
    setIsLoading(false);
    setError(null);
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  }, []);

  const handleError = useCallback(() => {
    setIsLoading(false);
    const errorMessage = 'Failed to load video stream';
    setError(errorMessage);
    onError?.(errorMessage);
  }, [onError]);

  const handlePlay = useCallback(() => {
    setIsPlaying(true);
    onPlay?.();
  }, [onPlay]);

  const handlePause = useCallback(() => {
    setIsPlaying(false);
    onPause?.();
  }, [onPause]);

  const handleTimeUpdate = useCallback(() => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  }, []);

  const handleVolumeChange = useCallback((newVolume: number) => {
    if (videoRef.current) {
      videoRef.current.volume = newVolume;
      setVolume(newVolume);
    }
  }, []);

  const handleMuteToggle = useCallback(() => {
    if (videoRef.current) {
      const newMuted = !isMuted;
      videoRef.current.muted = newMuted;
      setIsMuted(newMuted);
    }
  }, [isMuted]);

  const handleSeek = useCallback((time: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = time;
      setCurrentTime(time);
    }
  }, []);

  const handlePlayPause = useCallback(() => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play().catch(err => {
          console.warn('Play failed:', err);
          setError('Play failed');
        });
      }
    }
  }, [isPlaying]);

  const formatTime = (time: number): string => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  if (stream.status === 'disconnected' || stream.status === 'error') {
    return (
      <div className={`flex items-center justify-center bg-gray-900 text-white ${className}`}>
        <div className="text-center">
          <div className="text-3xl mb-2">
            {stream.status === 'error' ? '⚠️' : '📡'}
          </div>
          <div className="text-sm capitalize">{stream.status}</div>
          <div className="text-xs text-gray-400 mt-1">
            Drone {stream.droneId}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative bg-black ${className}`}>
      <video
        ref={videoRef}
        className="w-full h-full object-contain"
        onLoadedData={handleLoadedData}
        onError={handleError}
        onPlay={handlePlay}
        onPause={handlePause}
        onTimeUpdate={handleTimeUpdate}
        muted={isMuted}
        playsInline
      />

      {/* Loading overlay */}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50">
          <div className="text-white text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-2"></div>
            <div className="text-sm">Loading stream...</div>
          </div>
        </div>
      )}

      {/* Error overlay */}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-red-900 bg-opacity-75">
          <div className="text-white text-center">
            <div className="text-2xl mb-2">⚠️</div>
            <div className="text-sm">{error}</div>
            <button
              onClick={() => {
                setError(null);
                setIsLoading(true);
                if (videoRef.current) {
                  videoRef.current.load();
                }
              }}
              className="mt-2 px-3 py-1 bg-red-600 text-white rounded text-xs hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Stream info overlay */}
      <div className="absolute top-2 left-2 bg-black bg-opacity-50 text-white px-2 py-1 rounded text-xs">
        <div className="flex items-center space-x-2">
          <span>Drone {stream.droneId}</span>
          <div className={`w-2 h-2 rounded-full ${
            stream.status === 'connected' ? 'bg-green-500' :
            stream.status === 'connecting' ? 'bg-yellow-500' : 'bg-red-500'
          }`}></div>
        </div>
      </div>

      {/* Quality indicator */}
      <div className="absolute top-2 right-2 bg-black bg-opacity-50 text-white px-2 py-1 rounded text-xs">
        <span className="capitalize">{stream.quality}</span>
      </div>

      {/* Controls */}
      {showControls && !isLoading && !error && (
        <div className="absolute bottom-0 left-0 right-0">
          <VideoControls
            isPlaying={isPlaying}
            currentTime={currentTime}
            duration={duration}
            volume={volume}
            isMuted={isMuted}
            onPlayPause={handlePlayPause}
            onSeek={handleSeek}
            onVolumeChange={handleVolumeChange}
            onMuteToggle={handleMuteToggle}
          />

          {/* Progress bar */}
          <div className="bg-black bg-opacity-75 p-2">
            <div className="flex items-center space-x-2 text-xs text-white">
              <span>{formatTime(currentTime)}</span>
              <div className="flex-1 bg-gray-600 rounded-full h-1">
                <div
                  className="bg-blue-500 h-1 rounded-full transition-all"
                  style={{ width: `${duration > 0 ? (currentTime / duration) * 100 : 0}%` }}
                ></div>
              </div>
              <span>{formatTime(duration)}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};