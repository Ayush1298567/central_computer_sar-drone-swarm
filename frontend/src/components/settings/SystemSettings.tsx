import React, { useState, useEffect } from 'react';
import { Settings, Server, Database, Shield, Save, RefreshCw } from 'lucide-react';
import { SystemSettings as SystemSettingsType } from '../../types';
import { apiService } from '../../utils/api';

interface SystemSettingsProps {
  onClose?: () => void;
}

const SystemSettings: React.FC<SystemSettingsProps> = ({ onClose }) => {
  const [settings, setSettings] = useState<SystemSettingsType>({
    api_url: 'http://localhost:8000',
    websocket_url: 'ws://localhost:8000/ws',
    max_concurrent_missions: 10,
    default_search_altitude: 20,
    min_battery_level: 20,
    max_wind_speed: 15,
    enable_audio_alerts: true,
    enable_notifications: true,
    notification_volume: 50,
    auto_save_interval: 5,
  });

  const [originalSettings, setOriginalSettings] = useState<SystemSettingsType>(settings);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  useEffect(() => {
    // Check for unsaved changes
    const changed = JSON.stringify(settings) !== JSON.stringify(originalSettings);
    setHasUnsavedChanges(changed);
  }, [settings, originalSettings]);

  const loadSettings = async () => {
    setIsLoading(true);
    try {
      const systemSettings = await apiService.getSystemSettings();
      setSettings(systemSettings);
      setOriginalSettings(systemSettings);
    } catch (error) {
      console.error('Failed to load system settings:', error);
      // Keep default settings
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const result = await apiService.updateSystemSettings(settings);
      if (result.success) {
        setOriginalSettings(settings);
        setHasUnsavedChanges(false);
        alert('Settings saved successfully');
      } else {
        alert('Failed to save settings');
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
      alert('Failed to save settings');
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    if (confirm('Are you sure you want to reset all settings to their original values?')) {
      setSettings(originalSettings);
    }
  };

  const updateSetting = <K extends keyof SystemSettingsType>(key: K, value: SystemSettingsType[K]) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  if (isLoading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-2 text-gray-600">Loading settings...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Settings className="h-6 w-6 text-gray-600 mr-2" />
          <h2 className="text-xl font-bold text-gray-800">System Settings</h2>
        </div>
        <div className="flex items-center space-x-3">
          {hasUnsavedChanges && (
            <span className="text-sm text-orange-600 font-medium">Unsaved changes</span>
          )}
          <button
            onClick={handleReset}
            className="px-3 py-2 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md"
          >
            Reset
          </button>
          <button
            onClick={handleSave}
            disabled={!hasUnsavedChanges || isSaving}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-md text-sm font-medium flex items-center"
          >
            {isSaving ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Save Changes
              </>
            )}
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          )}
        </div>
      </div>

      {/* Settings Sections */}
      <div className="space-y-8">
        {/* API Configuration */}
        <div>
          <div className="flex items-center mb-4">
            <Server className="h-5 w-5 text-blue-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-800">API Configuration</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                API URL
              </label>
              <input
                type="url"
                value={settings.api_url}
                onChange={(e) => updateSetting('api_url', e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="http://localhost:8000"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                WebSocket URL
              </label>
              <input
                type="url"
                value={settings.websocket_url}
                onChange={(e) => updateSetting('websocket_url', e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="ws://localhost:8000/ws"
              />
            </div>
          </div>
        </div>

        {/* Mission Configuration */}
        <div>
          <div className="flex items-center mb-4">
            <Database className="h-5 w-5 text-green-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-800">Mission Configuration</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Concurrent Missions
              </label>
              <input
                type="number"
                min="1"
                max="50"
                value={settings.max_concurrent_missions}
                onChange={(e) => updateSetting('max_concurrent_missions', parseInt(e.target.value))}
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Default Search Altitude (m)
              </label>
              <input
                type="number"
                min="5"
                max="100"
                step="0.1"
                value={settings.default_search_altitude}
                onChange={(e) => updateSetting('default_search_altitude', parseFloat(e.target.value))}
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Auto Save Interval (minutes)
              </label>
              <input
                type="number"
                min="1"
                max="60"
                value={settings.auto_save_interval}
                onChange={(e) => updateSetting('auto_save_interval', parseInt(e.target.value))}
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-green-500 focus:border-green-500"
              />
            </div>
          </div>
        </div>

        {/* Safety Configuration */}
        <div>
          <div className="flex items-center mb-4">
            <Shield className="h-5 w-5 text-red-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-800">Safety Configuration</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Minimum Battery Level (%)
              </label>
              <input
                type="number"
                min="5"
                max="50"
                value={settings.min_battery_level}
                onChange={(e) => updateSetting('min_battery_level', parseFloat(e.target.value))}
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500 focus:border-red-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Maximum Wind Speed (m/s)
              </label>
              <input
                type="number"
                min="5"
                max="30"
                step="0.1"
                value={settings.max_wind_speed}
                onChange={(e) => updateSetting('max_wind_speed', parseFloat(e.target.value))}
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-red-500 focus:border-red-500"
              />
            </div>
          </div>
        </div>

        {/* Notification Configuration */}
        <div>
          <div className="flex items-center mb-4">
            <Settings className="h-5 w-5 text-purple-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-800">Notification Configuration</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.enable_notifications}
                  onChange={(e) => updateSetting('enable_notifications', e.target.checked)}
                  className="mr-3"
                />
                <span className="text-sm font-medium text-gray-700">Enable Notifications</span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.enable_audio_alerts}
                  onChange={(e) => updateSetting('enable_audio_alerts', e.target.checked)}
                  className="mr-3"
                />
                <span className="text-sm font-medium text-gray-700">Enable Audio Alerts</span>
              </label>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Notification Volume: {settings.notification_volume}%
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={settings.notification_volume}
                onChange={(e) => updateSetting('notification_volume', parseInt(e.target.value))}
                className="w-full"
              />
            </div>
          </div>
        </div>

        {/* Connection Test */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Connection Test</h3>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-700">API Connection Status</p>
                <p className="text-xs text-gray-500">Test connection to backend services</p>
              </div>
              <button
                onClick={async () => {
                  try {
                    const response = await fetch(`${settings.api_url}/health`);
                    const data = await response.json();
                    alert(`Connection successful! Server status: ${data.status}`);
                  } catch (error) {
                    alert('Connection failed. Please check your API URL.');
                  }
                }}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md text-sm font-medium"
              >
                Test Connection
              </button>
            </div>
          </div>
        </div>

        {/* Settings Summary */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-medium text-blue-800 mb-2">Settings Summary</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-blue-600 font-medium">API:</span>
              <p className="text-blue-700">{settings.api_url}</p>
            </div>
            <div>
              <span className="text-blue-600 font-medium">Max Missions:</span>
              <p className="text-blue-700">{settings.max_concurrent_missions}</p>
            </div>
            <div>
              <span className="text-blue-600 font-medium">Safety:</span>
              <p className="text-blue-700">{settings.min_battery_level}% min battery</p>
            </div>
            <div>
              <span className="text-blue-600 font-medium">Notifications:</span>
              <p className="text-blue-700">{settings.enable_notifications ? 'Enabled' : 'Disabled'}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemSettings;