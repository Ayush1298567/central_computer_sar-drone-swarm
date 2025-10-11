import React, { useState, useEffect } from 'react';
import { User, Palette, Globe, Bell, Monitor, Save, RefreshCw } from 'lucide-react';
import { UserPreferences as UserPreferencesType } from '../../types';
import { apiService } from '../../utils/api';

interface UserPreferencesProps {
  onClose?: () => void;
}

const UserPreferences: React.FC<UserPreferencesProps> = ({ onClose }) => {
  const [preferences, setPreferences] = useState<UserPreferencesType>({
    theme: 'auto',
    language: 'en',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    date_format: 'MM/DD/YYYY',
    notifications: {
      mission_updates: true,
      discovery_alerts: true,
      system_status: true,
      emergency_alerts: true,
    },
    dashboard: {
      default_view: 'overview',
      auto_refresh: true,
      refresh_interval: 30,
    },
  });

  const [originalPreferences, setOriginalPreferences] = useState<UserPreferencesType>(preferences);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  useEffect(() => {
    loadPreferences();
  }, []);

  useEffect(() => {
    // Check for unsaved changes
    const changed = JSON.stringify(preferences) !== JSON.stringify(originalPreferences);
    setHasUnsavedChanges(changed);
  }, [preferences, originalPreferences]);

  const loadPreferences = async () => {
    setIsLoading(true);
    try {
      const userPreferences = await apiService.getUserPreferences();
      setPreferences(userPreferences);
      setOriginalPreferences(userPreferences);
    } catch (error) {
      console.error('Failed to load user preferences:', error);
      // Keep default preferences
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const result = await apiService.updateUserPreferences(preferences);
      if (result.success) {
        setOriginalPreferences(preferences);
        setHasUnsavedChanges(false);
        alert('Preferences saved successfully');
      } else {
        alert('Failed to save preferences');
      }
    } catch (error) {
      console.error('Failed to save preferences:', error);
      alert('Failed to save preferences');
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    if (confirm('Are you sure you want to reset all preferences to their original values?')) {
      setPreferences(originalPreferences);
    }
  };

  const updatePreference = <K extends keyof UserPreferencesType>(key: K, value: UserPreferencesType[K]) => {
    setPreferences(prev => ({ ...prev, [key]: value }));
  };

  const updateNotificationPreference = (key: keyof UserPreferencesType['notifications'], value: boolean) => {
    setPreferences(prev => ({
      ...prev,
      notifications: { ...prev.notifications, [key]: value }
    }));
  };

  const updateDashboardPreference = (key: keyof UserPreferencesType['dashboard'], value: any) => {
    setPreferences(prev => ({
      ...prev,
      dashboard: { ...prev.dashboard, [key]: value }
    }));
  };

  if (isLoading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-2 text-gray-600">Loading preferences...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <User className="h-6 w-6 text-purple-600 mr-2" />
          <h2 className="text-xl font-bold text-gray-800">User Preferences</h2>
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
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white rounded-md text-sm font-medium flex items-center"
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
        {/* Appearance */}
        <div>
          <div className="flex items-center mb-4">
            <Palette className="h-5 w-5 text-blue-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-800">Appearance</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Theme
              </label>
              <select
                value={preferences.theme}
                onChange={(e) => updatePreference('theme', e.target.value as UserPreferencesType['theme'])}
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="light">Light</option>
                <option value="dark">Dark</option>
                <option value="auto">Auto (System)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Language
              </label>
              <select
                value={preferences.language}
                onChange={(e) => updatePreference('language', e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="en">English</option>
                <option value="es">Español</option>
                <option value="fr">Français</option>
                <option value="de">Deutsch</option>
                <option value="zh">中文</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Timezone
              </label>
              <select
                value={preferences.timezone}
                onChange={(e) => updatePreference('timezone', e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="America/New_York">Eastern Time</option>
                <option value="America/Chicago">Central Time</option>
                <option value="America/Denver">Mountain Time</option>
                <option value="America/Los_Angeles">Pacific Time</option>
                <option value="UTC">UTC</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Date Format
              </label>
              <select
                value={preferences.date_format}
                onChange={(e) => updatePreference('date_format', e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="MM/DD/YYYY">MM/DD/YYYY</option>
                <option value="DD/MM/YYYY">DD/MM/YYYY</option>
                <option value="YYYY-MM-DD">YYYY-MM-DD</option>
                <option value="DD MMM YYYY">DD MMM YYYY</option>
              </select>
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div>
          <div className="flex items-center mb-4">
            <Bell className="h-5 w-5 text-green-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-800">Notifications</h3>
          </div>
          <div className="space-y-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={preferences.notifications.mission_updates}
                onChange={(e) => updateNotificationPreference('mission_updates', e.target.checked)}
                className="mr-3"
              />
              <span className="text-sm font-medium text-gray-700">Mission Updates</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={preferences.notifications.discovery_alerts}
                onChange={(e) => updateNotificationPreference('discovery_alerts', e.target.checked)}
                className="mr-3"
              />
              <span className="text-sm font-medium text-gray-700">Discovery Alerts</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={preferences.notifications.system_status}
                onChange={(e) => updateNotificationPreference('system_status', e.target.checked)}
                className="mr-3"
              />
              <span className="text-sm font-medium text-gray-700">System Status</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={preferences.notifications.emergency_alerts}
                onChange={(e) => updateNotificationPreference('emergency_alerts', e.target.checked)}
                className="mr-3"
              />
              <span className="text-sm font-medium text-gray-700">Emergency Alerts</span>
            </label>
          </div>
        </div>

        {/* Dashboard */}
        <div>
          <div className="flex items-center mb-4">
            <Monitor className="h-5 w-5 text-orange-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-800">Dashboard</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Default View
              </label>
              <select
                value={preferences.dashboard.default_view}
                onChange={(e) => updateDashboardPreference('default_view', e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
              >
                <option value="overview">Overview</option>
                <option value="missions">Missions</option>
                <option value="drones">Drones</option>
                <option value="analytics">Analytics</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Auto Refresh Interval (seconds)
              </label>
              <input
                type="number"
                min="10"
                max="300"
                value={preferences.dashboard.refresh_interval}
                onChange={(e) => updateDashboardPreference('refresh_interval', parseInt(e.target.value))}
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                disabled={!preferences.dashboard.auto_refresh}
              />
            </div>
            <div className="md:col-span-2">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={preferences.dashboard.auto_refresh}
                  onChange={(e) => updateDashboardPreference('auto_refresh', e.target.checked)}
                  className="mr-3"
                />
                <span className="text-sm font-medium text-gray-700">Enable Auto Refresh</span>
              </label>
            </div>
          </div>
        </div>

        {/* Preview */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Preview</h3>
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Current Settings Preview</span>
              <span className="text-xs text-gray-500">
                Theme: {preferences.theme} • Language: {preferences.language}
              </span>
            </div>
            <div className="text-sm text-gray-600 space-y-1">
              <div>Timezone: {preferences.timezone}</div>
              <div>Date Format: {preferences.date_format}</div>
              <div>Dashboard View: {preferences.dashboard.default_view}</div>
              <div>Auto Refresh: {preferences.dashboard.auto_refresh ? `Every ${preferences.dashboard.refresh_interval}s` : 'Disabled'}</div>
            </div>
          </div>
        </div>

        {/* Reset to Defaults */}
        <div className="border-t border-gray-200 pt-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">Reset to Defaults</h3>
              <p className="text-sm text-gray-600">
                Reset all preferences to their default values.
              </p>
            </div>
            <button
              onClick={() => {
                if (confirm('Are you sure you want to reset all preferences to defaults? This will restore all settings to their original values.')) {
                  setPreferences({
                    theme: 'auto',
                    language: 'en',
                    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                    date_format: 'MM/DD/YYYY',
                    notifications: {
                      mission_updates: true,
                      discovery_alerts: true,
                      system_status: true,
                      emergency_alerts: true,
                    },
                    dashboard: {
                      default_view: 'overview',
                      auto_refresh: true,
                      refresh_interval: 30,
                    },
                  });
                }
              }}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md text-sm font-medium"
            >
              Reset to Defaults
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserPreferences;
