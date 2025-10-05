import React, { useState, useEffect } from 'react';
import { X, AlertTriangle, Info, CheckCircle, AlertCircle } from 'lucide-react';
import { Notification } from '../../types';

interface ToastNotificationsProps {
  notifications: Notification[];
  onNotificationClick?: (notification: Notification) => void;
  onPlaySound?: (priority: Notification['priority']) => void;
}

interface Toast {
  id: string;
  notification: Notification;
  position: { x: number; y: number };
  visible: boolean;
}

const ToastNotifications: React.FC<ToastNotificationsProps> = ({
  notifications,
  onNotificationClick,
  onPlaySound
}) => {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [nextPosition, setNextPosition] = useState({ x: 20, y: 20 });

  useEffect(() => {
    // Add new toasts for new notifications
    const existingIds = toasts.map(t => t.notification.id);
    const newNotifications = notifications.filter(n => !existingIds.includes(n.id));

    newNotifications.forEach(notification => {
      const newToast: Toast = {
        id: `toast-${notification.id}`,
        notification,
        position: { ...nextPosition },
        visible: true,
      };

      setToasts(prev => [...prev, newToast]);

      // Update next position (stack toasts)
      setNextPosition(prev => ({
        x: prev.x,
        y: prev.y + 80, // Stack vertically
      }));

      // Play sound
      onPlaySound?.(notification.priority);

      // Auto-remove after 5 seconds for non-critical notifications
      if (notification.priority !== 'critical' && notification.priority !== 'high') {
        setTimeout(() => {
          removeToast(newToast.id);
        }, 5000);
      }
    });
  }, [notifications, toasts, nextPosition, onPlaySound]);

  const removeToast = (toastId: string) => {
    setToasts(prev =>
      prev.map(toast =>
        toast.id === toastId ? { ...toast, visible: false } : toast
      )
    );

    // Remove from DOM after animation
    setTimeout(() => {
      setToasts(prev => prev.filter(toast => toast.id !== toastId));
    }, 300);
  };

  const handleNotificationClick = (notification: Notification) => {
    onNotificationClick?.(notification);
    removeToast(`toast-${notification.id}`);
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
      case 'critical': return <AlertTriangle className="h-5 w-5 text-red-600" />;
      case 'high': return <AlertCircle className="h-5 w-5 text-orange-600" />;
      case 'medium': return <Info className="h-5 w-5 text-yellow-600" />;
      case 'low': return <CheckCircle className="h-5 w-5 text-blue-600" />;
      default: return <Info className="h-5 w-5 text-gray-600" />;
    }
  };

  const getPriorityTextColor = (priority: Notification['priority']) => {
    switch (priority) {
      case 'critical': return 'text-red-800';
      case 'high': return 'text-orange-800';
      case 'medium': return 'text-yellow-800';
      case 'low': return 'text-blue-800';
      default: return 'text-gray-800';
    }
  };

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {toasts
        .filter(toast => toast.visible)
        .map(toast => (
          <div
            key={toast.id}
            className={`max-w-sm w-full ${getPriorityColor(toast.notification.priority)} border-l-4 rounded-lg shadow-lg transform transition-all duration-300 ${
              toast.visible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'
            }`}
            style={{
              position: 'fixed',
              top: `${toast.position.y}px`,
              right: `${toast.position.x}px`,
            }}
          >
            <div className="p-4">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  {getPriorityIcon(toast.notification.priority)}
                </div>
                <div className="ml-3 w-0 flex-1">
                  <div className="flex items-center justify-between">
                    <p className={`text-sm font-medium ${getPriorityTextColor(toast.notification.priority)}`}>
                      {toast.notification.title}
                    </p>
                    <div className="ml-4 flex-shrink-0 flex">
                      <button
                        onClick={() => removeToast(toast.id)}
                        className="inline-flex text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                  <div className="mt-1">
                    <p className="text-sm text-gray-600">
                      {toast.notification.message}
                    </p>
                  </div>
                  <div className="mt-2">
                    <button
                      onClick={() => handleNotificationClick(toast.notification)}
                      className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                    >
                      View Details →
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Progress bar for auto-dismiss */}
            {toast.notification.priority !== 'critical' && toast.notification.priority !== 'high' && (
              <div className="h-1 bg-gray-200">
                <div
                  className="h-full bg-gray-400 transition-all duration-5000 ease-linear"
                  style={{
                    width: '100%',
                    animation: 'toast-progress 5s linear forwards',
                  }}
                />
              </div>
            )}

            <style jsx>{`
              @keyframes toast-progress {
                from { width: 100%; }
                to { width: 0%; }
              }
            `}</style>
          </div>
        ))}
    </div>
  );
};

export default ToastNotifications;
