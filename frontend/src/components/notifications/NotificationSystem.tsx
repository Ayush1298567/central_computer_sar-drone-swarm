import React, { useState, useEffect } from 'react';
import { Bell, Volume2, VolumeX, Settings, X, Check } from 'lucide-react';
import { Notification } from '../../types';
import { apiService } from '../../utils/api';
import ToastNotifications from './ToastNotifications';
import CriticalAlerts from './CriticalAlerts';
import NotificationHistory from './NotificationHistory';

interface NotificationSystemProps {
  onNotificationClick?: (notification: Notification) => void;
}

const NotificationSystem: React.FC<NotificationSystemProps> = ({ onNotificationClick }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [notificationVolume, setNotificationVolume] = useState(50);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadNotifications();
    const interval = setInterval(loadNotifications, 10000); // Poll every 10 seconds
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Update unread count
    const unread = notifications.filter(n => !n.data?.read).length;
    setUnreadCount(unread);
  }, [notifications]);

  const loadNotifications = async () => {
    try {
      const notifications = await apiService.getNotifications();
      setNotifications(notifications);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    }
  };

  const handleMarkAsRead = async (notificationId: string) => {
    try {
      await apiService.markNotificationRead(notificationId);
      setNotifications(prev =>
        prev.map(n =>
          n.id === notificationId ? { ...n, data: { ...n.data, read: true } } : n
        )
      );
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const handleNotificationClick = (notification: Notification) => {
    if (!notification.data?.read) {
      handleMarkAsRead(notification.id);
    }
    onNotificationClick?.(notification);
  };

  const playNotificationSound = (priority: Notification['priority']) => {
    if (!audioEnabled) return;

    // Create audio context for notification sounds
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    // Different frequencies for different priorities
    const frequencies = {
      low: 400,
      medium: 600,
      high: 800,
      critical: 1000,
    };

    oscillator.frequency.setValueAtTime(frequencies[priority], audioContext.currentTime);
    gainNode.gain.setValueAtTime(notificationVolume / 100, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
  };

  const handleUpdatePreferences = async (preferences: any) => {
    try {
      await apiService.updateNotificationPreferences(preferences);
      setAudioEnabled(preferences.audio_alerts);
      setNotificationVolume(preferences.volume);
    } catch (error) {
      console.error('Failed to update notification preferences:', error);
    }
  };

  const getPriorityColor = (priority: Notification['priority']) => {
    switch (priority) {
      case 'critical': return 'border-red-500 bg-red-50';
      case 'high': return 'border-orange-500 bg-orange-50';
      case 'medium': return 'border-yellow-500 bg-yellow-50';
      case 'low': return 'border-blue-500 bg-blue-50';
      default: return 'border-gray-500 bg-gray-50';
    }
  };

  const getPriorityIcon = (priority: Notification['priority']) => {
    switch (priority) {
      case 'critical': return '🚨';
      case 'high': return '⚠️';
      case 'medium': return 'ℹ️';
      case 'low': return '💡';
      default: return '📢';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));

    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;

    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}h ago`;

    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  const criticalNotifications = notifications.filter(n => n.priority === 'critical');
  const highPriorityNotifications = notifications.filter(n => n.priority === 'high');
  const otherNotifications = notifications.filter(n => n.priority !== 'critical' && n.priority !== 'high');

  return (
    <div className="relative">
      {/* Notification Bell */}
      <button
        onClick={() => setShowHistory(!showHistory)}
        className="relative p-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
      >
        <Bell className="h-5 w-5 text-gray-600" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Settings Button */}
      <button
        onClick={() => setShowSettings(!showSettings)}
        className="ml-2 p-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
      >
        <Settings className="h-4 w-4 text-gray-600" />
      </button>

      {/* Notification History Panel */}
      {showHistory && (
        <div className="absolute right-0 top-full mt-2 w-96 max-h-96 bg-white border border-gray-200 rounded-lg shadow-lg z-50 overflow-hidden">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-800">Notifications</h3>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setAudioEnabled(!audioEnabled)}
                  className={`p-1 rounded ${audioEnabled ? 'text-blue-600' : 'text-gray-400'}`}
                >
                  {audioEnabled ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
                </button>
                <button
                  onClick={() => setShowHistory(false)}
                  className="p-1 text-gray-400 hover:text-gray-600"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>

          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                No notifications
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {/* Critical Notifications */}
                {criticalNotifications.map(notification => (
                  <div
                    key={notification.id}
                    onClick={() => handleNotificationClick(notification)}
                    className={`p-4 cursor-pointer hover:bg-gray-50 border-l-4 border-red-500 ${getPriorityColor(notification.priority)}`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center mb-1">
                          <span className="text-lg mr-2">{getPriorityIcon(notification.priority)}</span>
                          <span className="font-medium text-gray-800">{notification.title}</span>
                        </div>
                        <p className="text-sm text-gray-600 mb-1">{notification.message}</p>
                        <span className="text-xs text-gray-500">{formatTimestamp(notification.timestamp)}</span>
                      </div>
                      {!notification.data?.read && (
                        <div className="w-2 h-2 bg-blue-500 rounded-full mt-1" />
                      )}
                    </div>
                  </div>
                ))}

                {/* High Priority Notifications */}
                {highPriorityNotifications.map(notification => (
                  <div
                    key={notification.id}
                    onClick={() => handleNotificationClick(notification)}
                    className={`p-4 cursor-pointer hover:bg-gray-50 border-l-4 border-orange-500 ${getPriorityColor(notification.priority)}`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center mb-1">
                          <span className="text-lg mr-2">{getPriorityIcon(notification.priority)}</span>
                          <span className="font-medium text-gray-800">{notification.title}</span>
                        </div>
                        <p className="text-sm text-gray-600 mb-1">{notification.message}</p>
                        <span className="text-xs text-gray-500">{formatTimestamp(notification.timestamp)}</span>
                      </div>
                      {!notification.data?.read && (
                        <div className="w-2 h-2 bg-blue-500 rounded-full mt-1" />
                      )}
                    </div>
                  </div>
                ))}

                {/* Other Notifications */}
                {otherNotifications.slice(0, 10).map(notification => (
                  <div
                    key={notification.id}
                    onClick={() => handleNotificationClick(notification)}
                    className={`p-3 cursor-pointer hover:bg-gray-50 ${getPriorityColor(notification.priority)}`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center mb-1">
                          <span className="text-sm mr-2">{getPriorityIcon(notification.priority)}</span>
                          <span className="text-sm font-medium text-gray-800">{notification.title}</span>
                        </div>
                        <p className="text-xs text-gray-600 mb-1">{notification.message}</p>
                        <span className="text-xs text-gray-500">{formatTimestamp(notification.timestamp)}</span>
                      </div>
                      {!notification.data?.read && (
                        <div className="w-2 h-2 bg-blue-500 rounded-full mt-1" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Settings Panel */}
      {showSettings && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-50 p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-800">Notification Settings</h3>
            <button
              onClick={() => setShowSettings(false)}
              className="p-1 text-gray-400 hover:text-gray-600"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={audioEnabled}
                  onChange={(e) => setAudioEnabled(e.target.checked)}
                  className="mr-2"
                />
                <span className="text-sm font-medium text-gray-700">Enable Audio Alerts</span>
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Notification Volume: {notificationVolume}%
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={notificationVolume}
                onChange={(e) => setNotificationVolume(parseInt(e.target.value))}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Alert Priorities
              </label>
              <div className="space-y-2">
                {['critical', 'high', 'medium', 'low'].map(priority => (
                  <label key={priority} className="flex items-center">
                    <input
                      type="checkbox"
                      defaultChecked={priority === 'critical' || priority === 'high'}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-600 capitalize">{priority} priority notifications</span>
                  </label>
                ))}
              </div>
            </div>

            <button
              onClick={() => handleUpdatePreferences({
                audio_alerts: audioEnabled,
                volume: notificationVolume,
                critical_alerts: true,
                high_priority_alerts: true,
                medium_priority_alerts: false,
                low_priority_alerts: false,
              })}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md font-medium"
            >
              Save Settings
            </button>
          </div>
        </div>
      )}

      {/* Toast Notifications */}
      <ToastNotifications
        notifications={notifications.filter(n => n.priority !== 'critical')}
        onNotificationClick={handleNotificationClick}
        onPlaySound={playNotificationSound}
      />

      {/* Critical Alerts */}
      <CriticalAlerts
        notifications={criticalNotifications}
        onNotificationClick={handleNotificationClick}
        onPlaySound={playNotificationSound}
      />

      {/* Click outside to close */}
      {(showHistory || showSettings) && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => {
            setShowHistory(false);
            setShowSettings(false);
          }}
        />
      )}
    </div>
  );
};

export default NotificationSystem;