import React, { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import { Play, Square, RotateCcw, Settings, Activity } from 'lucide-react';

interface SimulatorControlsProps {
  isConnected: boolean;
  isRunning: boolean;
  onStart: () => void;
  onStop: () => void;
  onReset: () => void;
  onSettingsChange?: (settings: SimulatorSettings) => void;
}

interface SimulatorSettings {
  updateInterval: number;
  enableWind: boolean;
  enableBatteryDrain: boolean;
  enableDiscoveries: boolean;
  windSpeed: number;
  discoveryRate: number;
}

const SimulatorControls: React.FC<SimulatorControlsProps> = ({
  isConnected,
  isRunning,
  onStart,
  onStop,
  onReset,
  onSettingsChange
}) => {
  const [settings, setSettings] = useState<SimulatorSettings>({
    updateInterval: 100,
    enableWind: true,
    enableBatteryDrain: true,
    enableDiscoveries: true,
    windSpeed: 2.0,
    discoveryRate: 0.1
  });

  const [showSettings, setShowSettings] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    if (isRunning) {
      const interval = setInterval(() => {
        setLastUpdate(new Date());
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [isRunning]);

  const handleSettingsChange = (key: keyof SimulatorSettings, value: any) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    onSettingsChange?.(newSettings);
  };

  const getStatusColor = () => {
    if (!isConnected) return 'destructive';
    if (isRunning) return 'default';
    return 'secondary';
  };

  const getStatusText = () => {
    if (!isConnected) return 'Disconnected';
    if (isRunning) return 'Running';
    return 'Stopped';
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="w-5 h-5" />
          Drone Simulator Controls
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Status Display */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Badge variant={getStatusColor()}>
              {getStatusText()}
            </Badge>
            {lastUpdate && isRunning && (
              <span className="text-sm text-muted-foreground">
                Last update: {lastUpdate.toLocaleTimeString()}
              </span>
            )}
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowSettings(!showSettings)}
          >
            <Settings className="w-4 h-4" />
          </Button>
        </div>

        {/* Control Buttons */}
        <div className="flex gap-2">
          <Button
            onClick={onStart}
            disabled={!isConnected || isRunning}
            className="flex-1"
          >
            <Play className="w-4 h-4 mr-2" />
            Start Simulation
          </Button>
          <Button
            onClick={onStop}
            disabled={!isRunning}
            variant="destructive"
            className="flex-1"
          >
            <Square className="w-4 h-4 mr-2" />
            Stop Simulation
          </Button>
          <Button
            onClick={onReset}
            disabled={isRunning}
            variant="outline"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Reset
          </Button>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <Card className="border-2">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Simulation Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">Update Interval (ms)</label>
                  <input
                    type="number"
                    value={settings.updateInterval}
                    onChange={(e) => handleSettingsChange('updateInterval', parseInt(e.target.value))}
                    className="w-full mt-1 px-3 py-2 border rounded-md"
                    min="50"
                    max="1000"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Wind Speed (m/s)</label>
                  <input
                    type="number"
                    value={settings.windSpeed}
                    onChange={(e) => handleSettingsChange('windSpeed', parseFloat(e.target.value))}
                    className="w-full mt-1 px-3 py-2 border rounded-md"
                    min="0"
                    max="20"
                    step="0.1"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium">Discovery Rate</label>
                  <input
                    type="number"
                    value={settings.discoveryRate}
                    onChange={(e) => handleSettingsChange('discoveryRate', parseFloat(e.target.value))}
                    className="w-full mt-1 px-3 py-2 border rounded-md"
                    min="0"
                    max="1"
                    step="0.01"
                  />
                </div>
                <div className="text-sm text-muted-foreground mt-8">
                  {Math.round(settings.discoveryRate * 100)}% per waypoint
                </div>
              </div>

              <div className="space-y-2">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={settings.enableWind}
                    onChange={(e) => handleSettingsChange('enableWind', e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-sm">Enable Wind Effects</span>
                </label>

                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={settings.enableBatteryDrain}
                    onChange={(e) => handleSettingsChange('enableBatteryDrain', e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-sm">Enable Battery Drain</span>
                </label>

                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={settings.enableDiscoveries}
                    onChange={(e) => handleSettingsChange('enableDiscoveries', e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-sm">Enable Object Discoveries</span>
                </label>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Connection Status Alert */}
        {!isConnected && (
          <Alert>
            <AlertDescription>
              Simulator is not connected. Please check your connection settings.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default SimulatorControls;
