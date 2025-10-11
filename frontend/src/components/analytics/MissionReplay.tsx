import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, RotateCcw, FastForward, Rewind, Volume2, VolumeX, MapPin, Clock } from 'lucide-react';
import { Mission, Drone } from '../../types';
import { apiService } from '../../utils/api';

interface MissionReplayProps {
  mission: Mission;
  drones: Drone[];
  onClose?: () => void;
}

interface ReplayEvent {
  timestamp: string;
  type: 'drone_position' | 'discovery' | 'emergency' | 'status_change' | 'command';
  droneId?: string;
  data: any;
  description: string;
}

const MissionReplay: React.FC<MissionReplayProps> = ({ mission, drones, onClose }) => {
  const [replayEvents, setReplayEvents] = useState<ReplayEvent[]>([]);
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [selectedEvent, setSelectedEvent] = useState<ReplayEvent | null>(null);
  const [maxTime, setMaxTime] = useState(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    loadReplayData();
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [mission.id]);

  useEffect(() => {
    if (isPlaying && maxTime > 0) {
      intervalRef.current = setInterval(() => {
        setCurrentTime(prev => {
          if (prev >= maxTime) {
            setIsPlaying(false);
            return maxTime;
          }
          return prev + (100 * playbackSpeed); // Update every 100ms
        });
      }, 100);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isPlaying, playbackSpeed, maxTime]);

  const loadReplayData = async () => {
    try {
      const replayData = await apiService.getMissionReplay(mission.id);

      // Convert replay data to events
      const events: ReplayEvent[] = [];
      let currentTimeMs = 0;

      // Simulate mission timeline with mock events
      const missionDuration = (mission.estimated_duration || 60) * 60 * 1000; // Convert to milliseconds

      // Add mission start event
      events.push({
        timestamp: new Date(Date.now() - missionDuration).toISOString(),
        type: 'status_change',
        data: { status: 'started' },
        description: 'Mission started'
      });

      // Add drone takeoff events
      mission.assigned_drone_count = mission.assigned_drone_count || 1;
      for (let i = 0; i < mission.assigned_drone_count; i++) {
        events.push({
          timestamp: new Date(Date.now() - missionDuration + (i * 5000)).toISOString(),
          type: 'status_change',
          droneId: `drone-${i + 1}`,
          data: { status: 'flying' },
          description: `Drone ${i + 1} took off`
        });
      }

      // Add position updates (every 30 seconds)
      for (let i = 0; i < missionDuration / 30000; i++) {
        const timestamp = new Date(Date.now() - missionDuration + (i * 30000)).toISOString();
        events.push({
          timestamp: timestamp,
          type: 'drone_position',
          droneId: `drone-${Math.floor(Math.random() * mission.assigned_drone_count) + 1}`,
          data: {
            lat: 40.7128 + (Math.random() - 0.5) * 0.01,
            lng: -74.0060 + (Math.random() - 0.5) * 0.01,
            alt: 20 + Math.random() * 10
          },
          description: 'Position update'
        });
      }

      // Add some discovery events
      const discoveryCount = Math.floor(Math.random() * 3);
      for (let i = 0; i < discoveryCount; i++) {
        const discoveryTime = missionDuration * (0.3 + Math.random() * 0.5);
        events.push({
          timestamp: new Date(Date.now() - missionDuration + discoveryTime).toISOString(),
          type: 'discovery',
          droneId: `drone-${Math.floor(Math.random() * mission.assigned_drone_count) + 1}`,
          data: {
            object_type: ['person', 'vehicle', 'debris'][Math.floor(Math.random() * 3)],
            confidence: 0.7 + Math.random() * 0.3,
            lat: 40.7128 + (Math.random() - 0.5) * 0.01,
            lng: -74.0060 + (Math.random() - 0.5) * 0.01
          },
          description: 'Object detected'
        });
      }

      // Add mission completion
      events.push({
        timestamp: new Date().toISOString(),
        type: 'status_change',
        data: { status: 'completed' },
        description: 'Mission completed'
      });

      events.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

      setReplayEvents(events);
      setMaxTime(missionDuration);
      setCurrentTime(0);
    } catch (error) {
      console.error('Failed to load replay data:', error);
      // Create mock data
      setReplayEvents([
        {
          timestamp: new Date().toISOString(),
          type: 'status_change',
          data: { status: 'started' },
          description: 'Mission started'
        }
      ]);
      setMaxTime(60000); // 1 minute for demo
    }
  };

  const handlePlay = () => {
    setIsPlaying(!isPlaying);
  };

  const handleReset = () => {
    setCurrentTime(0);
    setIsPlaying(false);
    setSelectedEvent(null);
  };

  const handleSpeedChange = (speed: number) => {
    setPlaybackSpeed(speed);
  };

  const handleTimelineClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = x / rect.width;
    setCurrentTime(percentage * maxTime);
  };

  const formatTime = (ms: number) => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
      return `${hours}:${(minutes % 60).toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`;
    }
    return `${minutes}:${(seconds % 60).toString().padStart(2, '0')}`;
  };

  const currentEvents = replayEvents.filter(event =>
    new Date(event.timestamp).getTime() <= currentTime + new Date(mission.created_at).getTime()
  );

  const progressPercentage = maxTime > 0 ? (currentTime / maxTime) * 100 : 0;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-800">Mission Replay</h2>
          <p className="text-sm text-gray-600">{mission.name}</p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600"
          >
            ×
          </button>
        )}
      </div>

      {/* Controls */}
      <div className="flex items-center space-x-4 mb-6">
        <button
          onClick={handlePlay}
          className="p-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
        >
          {isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
        </button>

        <button
          onClick={handleReset}
          className="p-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg"
        >
          <RotateCcw className="h-4 w-4" />
        </button>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => handleSpeedChange(0.5)}
            className={`px-3 py-1 rounded text-sm ${playbackSpeed === 0.5 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'}`}
          >
            0.5x
          </button>
          <button
            onClick={() => handleSpeedChange(1)}
            className={`px-3 py-1 rounded text-sm ${playbackSpeed === 1 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'}`}
          >
            1x
          </button>
          <button
            onClick={() => handleSpeedChange(2)}
            className={`px-3 py-1 rounded text-sm ${playbackSpeed === 2 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700'}`}
          >
            2x
          </button>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setAudioEnabled(!audioEnabled)}
            className={`p-2 rounded ${audioEnabled ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-400'}`}
          >
            {audioEnabled ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
          </button>
        </div>

        <div className="flex-1">
          <div className="text-sm text-gray-600 mb-1">
            {formatTime(currentTime)} / {formatTime(maxTime)}
          </div>
          <div
            className="w-full h-2 bg-gray-200 rounded-full cursor-pointer"
            onClick={handleTimelineClick}
          >
            <div
              className="h-full bg-blue-600 rounded-full transition-all duration-100"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Map Area (Placeholder) */}
        <div className="bg-gray-100 rounded-lg p-4 h-64 flex items-center justify-center">
          <div className="text-center">
            <MapPin className="h-12 w-12 text-gray-400 mx-auto mb-2" />
            <p className="text-gray-600">Map visualization would be displayed here</p>
            <p className="text-sm text-gray-500 mt-1">
              Showing drone positions and events at {formatTime(currentTime)}
            </p>
          </div>
        </div>

        {/* Events Timeline */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-800">Events Timeline</h3>
          <div className="max-h-64 overflow-y-auto space-y-2">
            {currentEvents.map((event, index) => (
              <div
                key={index}
                className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                  selectedEvent === event ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-white hover:bg-gray-50'
                }`}
                onClick={() => setSelectedEvent(event)}
              >
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 mt-1">
                    {event.type === 'drone_position' && <MapPin className="h-4 w-4 text-blue-600" />}
                    {event.type === 'discovery' && <div className="h-4 w-4 bg-green-500 rounded-full" />}
                    {event.type === 'emergency' && <div className="h-4 w-4 bg-red-500 rounded-full" />}
                    {event.type === 'status_change' && <Clock className="h-4 w-4 text-gray-600" />}
                    {event.type === 'command' && <div className="h-4 w-4 bg-purple-500 rounded-full" />}
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-800">{event.description}</p>
                    <p className="text-xs text-gray-500">
                      {event.droneId && `Drone ${event.droneId} • `}
                      {formatTime(new Date(event.timestamp).getTime() - new Date(mission.created_at).getTime())}
                    </p>
                    {event.type === 'discovery' && (
                      <div className="mt-1 text-xs text-green-700">
                        {event.data.object_type} detected ({(event.data.confidence * 100).toFixed(0)}% confidence)
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Event Details */}
      {selectedEvent && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="text-lg font-semibold text-gray-800 mb-2">Event Details</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Event Type</p>
              <p className="font-medium">{selectedEvent.type.replace('_', ' ').toUpperCase()}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Timestamp</p>
              <p className="font-medium">{new Date(selectedEvent.timestamp).toLocaleString()}</p>
            </div>
            {selectedEvent.droneId && (
              <div>
                <p className="text-sm text-gray-600">Drone</p>
                <p className="font-medium">{selectedEvent.droneId}</p>
              </div>
            )}
            <div>
              <p className="text-sm text-gray-600">Description</p>
              <p className="font-medium">{selectedEvent.description}</p>
            </div>
          </div>

          {selectedEvent.data && (
            <div className="mt-4">
              <p className="text-sm text-gray-600 mb-2">Event Data</p>
              <pre className="bg-white p-3 rounded text-xs overflow-x-auto">
                {JSON.stringify(selectedEvent.data, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Statistics */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4 pt-6 border-t border-gray-200">
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-600">{currentEvents.length}</div>
          <div className="text-sm text-gray-600">Events</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">
            {currentEvents.filter(e => e.type === 'discovery').length}
          </div>
          <div className="text-sm text-gray-600">Discoveries</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-orange-600">
            {mission.assigned_drone_count}
          </div>
          <div className="text-sm text-gray-600">Drones</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-purple-600">
            {(currentTime / maxTime * 100).toFixed(1)}%
          </div>
          <div className="text-sm text-gray-600">Progress</div>
        </div>
      </div>
    </div>
  );
};

export default MissionReplay;
