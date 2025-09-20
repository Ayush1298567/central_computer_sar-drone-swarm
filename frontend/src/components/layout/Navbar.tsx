import React from 'react';
import { Bell, Settings, User, Wifi, WifiOff } from 'lucide-react';

const Navbar: React.FC = () => {
  const [isConnected] = React.useState(true);

  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Logo and Title */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">SAR</span>
            </div>
            <h1 className="text-xl font-semibold text-gray-900">
              Mission Commander
            </h1>
          </div>
        </div>

        {/* Status and Actions */}
        <div className="flex items-center space-x-4">
          {/* Connection Status */}
          <div className="flex items-center space-x-2">
            {isConnected ? (
              <Wifi className="w-5 h-5 text-green-500" />
            ) : (
              <WifiOff className="w-5 h-5 text-red-500" />
            )}
            <span className={`text-sm font-medium ${
              isConnected ? 'text-green-600' : 'text-red-600'
            }`}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>

          {/* System Time */}
          <div className="text-sm text-gray-600">
            {new Date().toLocaleTimeString()}
          </div>

          {/* Notifications */}
          <button className="relative p-2 text-gray-400 hover:text-gray-600 transition-colors">
            <Bell className="w-5 h-5" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>

          {/* Settings */}
          <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
            <Settings className="w-5 h-5" />
          </button>

          {/* User Profile */}
          <button className="flex items-center space-x-2 p-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
            <User className="w-5 h-5" />
            <span className="text-sm font-medium">Operator</span>
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;