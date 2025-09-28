import React, { useState, useEffect } from 'react';
import { X, AlertTriangle, Volume2, VolumeX } from 'lucide-react';
import { Notification } from '../../types';

interface CriticalAlertsProps {
  notifications: Notification[];
  onNotificationClick?: (notification: Notification) => void;
  onPlaySound?: (priority: Notification['priority']) => void;
}

interface CriticalAlert {
  id: string;
  notification: Notification;
  visible: boolean;
  acknowledged: boolean;
}

const CriticalAlerts: React.FC<CriticalAlertsProps> = ({
  notifications,
  onNotificationClick,
  onPlaySound
}) => {
  const [alerts, setAlerts] = useState<CriticalAlert[]>([]);
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [soundInterval, setSoundInterval] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Add new critical alerts
    const existingIds = alerts.map(a => a.notification.id);
    const newNotifications = notifications.filter(n => !existingIds.includes(n.id));

    newNotifications.forEach(notification => {
      const newAlert: CriticalAlert = {
        id: `alert-${notification.id}`,
        notification,
        visible: true,
        acknowledged: false,
      };

      setAlerts(prev => [...prev, newAlert]);

      // Play critical alert sound repeatedly
      if (audioEnabled) {
        startCriticalAlertSound();
      }
    });

    // Clean up old alerts (keep only last 5)
    if (alerts.length > 5) {
      setAlerts(prev => prev.slice(-5));
    }
  }, [notifications, alerts, audioEnabled]);

  const startCriticalAlertSound = () => {
    if (soundInterval) {
      clearInterval(soundInterval);
    }

    const interval = setInterval(() => {
      onPlaySound?.('critical');
    }, 1000); // Beep every second

    setSoundInterval(interval);

    // Stop after 30 seconds if not acknowledged
    setTimeout(() => {
      if (soundInterval) {
        clearInterval(soundInterval);
        setSoundInterval(null);
      }
    }, 30000);
  };

  const stopCriticalAlertSound = () => {
    if (soundInterval) {
      clearInterval(soundInterval);
      setSoundInterval(null);
    }
  };

  const acknowledgeAlert = (alertId: string) => {
    setAlerts(prev =>
      prev.map(alert =>
        alert.id === alertId ? { ...alert, acknowledged: true } : alert
      )
    );

    // Stop sound for this alert
    stopCriticalAlertSound();
  };

  const dismissAlert = (alertId: string) => {
    setAlerts(prev =>
      prev.map(alert =>
        alert.id === alertId ? { ...alert, visible: false } : alert
      )
    );

    // Remove from DOM after animation
    setTimeout(() => {
      setAlerts(prev => prev.filter(alert => alert.id !== alertId));
    }, 500);
  };

  const handleNotificationClick = (notification: Notification) => {
    acknowledgeAlert(`alert-${notification.id}`);
    onNotificationClick?.(notification);
  };

  // Auto-dismiss acknowledged alerts after 10 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      const acknowledgedAlerts = alerts.filter(alert => alert.acknowledged);
      acknowledgedAlerts.forEach(alert => {
        setTimeout(() => {
          dismissAlert(alert.id);
        }, 10000);
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [alerts]);

  const unacknowledgedAlerts = alerts.filter(alert => !alert.acknowledged && alert.visible);
  const acknowledgedAlerts = alerts.filter(alert => alert.acknowledged && alert.visible);

  return (
    <div className="fixed inset-0 z-50 pointer-events-none">
      {/* Critical Alert Modals */}
      {unacknowledgedAlerts.map((alert, index) => (
        <div
          key={alert.id}
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center pointer-events-auto"
          style={{ zIndex: 1000 + index }}
        >
          <div className="bg-white rounded-lg shadow-2xl max-w-md w-full mx-4 overflow-hidden">
            {/* Header with pulsing red border */}
            <div className="bg-red-600 text-white p-4 relative">
              <div className="absolute inset-0 bg-red-500 animate-pulse opacity-20"></div>
              <div className="relative flex items-center">
                <AlertTriangle className="h-8 w-8 mr-3 animate-pulse" />
                <div>
                  <h3 className="text-xl font-bold">CRITICAL ALERT</h3>
                  <p className="text-red-100 text-sm">{alert.notification.type.toUpperCase()}</p>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="p-6">
              <h4 className="text-lg font-semibold text-gray-800 mb-2">
                {alert.notification.title}
              </h4>
              <p className="text-gray-600 mb-4">
                {alert.notification.message}
              </p>

              {alert.notification.data && (
                <div className="bg-gray-50 rounded p-3 mb-4">
                  <h5 className="font-medium text-gray-800 mb-2">Alert Details:</h5>
                  <div className="text-sm text-gray-600 space-y-1">
                    {Object.entries(alert.notification.data).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="capitalize">{key.replace('_', ' ')}:</span>
                        <span className="font-medium">{String(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex space-x-3">
                <button
                  onClick={() => handleNotificationClick(alert.notification)}
                  className="flex-1 bg-red-600 hover:bg-red-700 text-white py-3 px-4 rounded-md font-semibold flex items-center justify-center"
                >
                  <AlertTriangle className="h-5 w-5 mr-2" />
                  Respond Now
                </button>
                <button
                  onClick={() => acknowledgeAlert(alert.id)}
                  className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-3 px-4 rounded-md font-semibold"
                >
                  Acknowledge
                </button>
              </div>

              {/* Audio Control */}
              <div className="mt-4 flex items-center justify-center">
                <button
                  onClick={() => setAudioEnabled(!audioEnabled)}
                  className={`p-2 rounded-full ${audioEnabled ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-400'}`}
                >
                  {audioEnabled ? <Volume2 className="h-5 w-5" /> : <VolumeX className="h-5 w-5" />}
                </button>
                <span className="ml-2 text-sm text-gray-600">
                  {audioEnabled ? 'Audio alerts enabled' : 'Audio alerts disabled'}
                </span>
              </div>
            </div>
          </div>
        </div>
      ))}

      {/* Acknowledged Alerts (smaller, less intrusive) */}
      {acknowledgedAlerts.map((alert, index) => (
        <div
          key={alert.id}
          className="fixed top-4 left-4 bg-green-50 border border-green-200 rounded-lg shadow-lg p-4 pointer-events-auto max-w-sm"
          style={{ zIndex: 900 + index }}
        >
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <AlertTriangle className="h-5 w-5 text-green-600" />
            </div>
            <div className="ml-3 w-0 flex-1">
              <p className="text-sm font-medium text-green-800">
                Alert Acknowledged
              </p>
              <p className="mt-1 text-sm text-green-700">
                {alert.notification.message}
              </p>
            </div>
            <div className="ml-4 flex-shrink-0 flex">
              <button
                onClick={() => dismissAlert(alert.id)}
                className="inline-flex text-green-400 hover:text-green-600"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      ))}

      {/* Background overlay for unacknowledged alerts */}
      {unacknowledgedAlerts.length > 0 && (
        <div className="fixed inset-0 bg-black bg-opacity-25 pointer-events-none" />
      )}
    </div>
  );
};

export default CriticalAlerts;