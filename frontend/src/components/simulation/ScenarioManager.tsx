import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Textarea } from '../ui/textarea';
import { Alert, AlertDescription } from '../ui/alert';
import {
  Plus,
  Trash2,
  MapPin,
  Users,
  Building,
  Car,
  Anchor,
  TreePine,
  AlertTriangle,
  CheckCircle,
  Eye
} from 'lucide-react';

interface ScenarioObject {
  id: string;
  type: 'person' | 'vehicle' | 'building' | 'boat' | 'structure';
  latitude: number;
  longitude: number;
  altitude: number;
  mobile: boolean;
  confidence: number;
}

interface Scenario {
  id: string;
  name: string;
  description: string;
  type: string;
  objects: ScenarioObject[];
  areaSize: { width: number; height: number };
  environmentalConditions: {
    weather: string;
    lighting: string;
    visibility: number;
  };
}

interface ScenarioManagerProps {
  scenarios: Scenario[];
  activeScenario?: string;
  onCreateScenario: (scenario: Omit<Scenario, 'id'>) => void;
  onLoadScenario: (scenarioId: string) => void;
  onDeleteScenario: (scenarioId: string) => void;
  onUpdateScenario: (scenario: Scenario) => void;
}

const ScenarioManager: React.FC<ScenarioManagerProps> = ({
  scenarios,
  activeScenario,
  onCreateScenario,
  onLoadScenario,
  onDeleteScenario,
  onUpdateScenario
}) => {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newScenario, setNewScenario] = useState({
    name: '',
    description: '',
    type: 'building_collapse',
    objects: [] as ScenarioObject[],
    areaSize: { width: 500, height: 500 },
    environmentalConditions: {
      weather: 'clear',
      lighting: 'good',
      visibility: 10000
    }
  });

  const [newObject, setNewObject] = useState({
    type: 'person' as ScenarioObject['type'],
    latitude: 40.7128,
    longitude: -74.0060,
    altitude: 0,
    mobile: false,
    confidence: 0.8
  });

  const scenarioTypes = [
    { value: 'building_collapse', label: 'Building Collapse', icon: Building },
    { value: 'wilderness_search', label: 'Wilderness Search', icon: TreePine },
    { value: 'maritime_search', label: 'Maritime Search', icon: Anchor },
    { value: 'traffic_accident', label: 'Traffic Accident', icon: Car },
    { value: 'missing_person', label: 'Missing Person', icon: Users }
  ];

  const objectTypes = [
    { value: 'person', label: 'Person', icon: Users },
    { value: 'vehicle', label: 'Vehicle', icon: Car },
    { value: 'building', label: 'Building', icon: Building },
    { value: 'boat', label: 'Boat', icon: Anchor },
    { value: 'structure', label: 'Structure', icon: Building }
  ];

  const weatherConditions = [
    { value: 'clear', label: 'Clear' },
    { value: 'cloudy', label: 'Cloudy' },
    { value: 'rainy', label: 'Rainy' },
    { value: 'foggy', label: 'Foggy' },
    { value: 'night', label: 'Night' }
  ];

  const lightingConditions = [
    { value: 'good', label: 'Good' },
    { value: 'poor', label: 'Poor' },
    { value: 'night', label: 'Night' }
  ];

  const handleCreateScenario = () => {
    if (!newScenario.name.trim()) {
      alert('Please enter a scenario name');
      return;
    }

    onCreateScenario(newScenario);
    setNewScenario({
      name: '',
      description: '',
      type: 'building_collapse',
      objects: [],
      areaSize: { width: 500, height: 500 },
      environmentalConditions: {
        weather: 'clear',
        lighting: 'good',
        visibility: 10000
      }
    });
    setShowCreateForm(false);
  };

  const handleAddObject = () => {
    const object: ScenarioObject = {
      id: `obj_${Date.now()}`,
      ...newObject
    };

    setNewScenario(prev => ({
      ...prev,
      objects: [...prev.objects, object]
    }));

    setNewObject({
      type: 'person',
      latitude: 40.7128,
      longitude: -74.0060,
      altitude: 0,
      mobile: false,
      confidence: 0.8
    });
  };

  const handleRemoveObject = (objectId: string) => {
    setNewScenario(prev => ({
      ...prev,
      objects: prev.objects.filter(obj => obj.id !== objectId)
    }));
  };

  const getScenarioIcon = (type: string) => {
    const scenarioType = scenarioTypes.find(t => t.value === type);
    if (scenarioType) {
      const IconComponent = scenarioType.icon;
      return <IconComponent className="w-4 h-4" />;
    }
    return <MapPin className="w-4 h-4" />;
  };

  const getObjectIcon = (type: string) => {
    const objectType = objectTypes.find(t => t.value === type);
    if (objectType) {
      const IconComponent = objectType.icon;
      return <IconComponent className="w-4 h-4" />;
    }
    return <MapPin className="w-4 h-4" />;
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MapPin className="w-5 h-5" />
            Scenario Manager
          </div>
          <Button
            onClick={() => setShowCreateForm(!showCreateForm)}
            size="sm"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Scenario
          </Button>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Scenario List */}
        {scenarios.length > 0 && (
          <div className="space-y-2">
            <h3 className="font-medium text-sm">Available Scenarios</h3>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {scenarios.map(scenario => (
                <div
                  key={scenario.id}
                  className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                    activeScenario === scenario.id ? 'border-blue-500 bg-blue-50' : 'hover:bg-gray-50'
                  }`}
                  onClick={() => onLoadScenario(scenario.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {getScenarioIcon(scenario.type)}
                      <div>
                        <div className="font-medium">{scenario.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {scenario.objects.length} objects • {scenario.type.replace('_', ' ')}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {activeScenario === scenario.id && (
                        <Badge variant="default">Active</Badge>
                      )}
                      <Button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteScenario(scenario.id);
                        }}
                        variant="outline"
                        size="sm"
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Create Scenario Form */}
        {showCreateForm && (
          <div className="border rounded-lg p-4 space-y-4">
            <h3 className="font-medium">Create New Scenario</h3>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="scenario-name">Scenario Name</Label>
                <Input
                  id="scenario-name"
                  value={newScenario.name}
                  onChange={(e) => setNewScenario(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Enter scenario name"
                />
              </div>
              <div>
                <Label htmlFor="scenario-type">Scenario Type</Label>
                <Select
                  value={newScenario.type}
                  onValueChange={(value) => setNewScenario(prev => ({ ...prev, type: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {scenarioTypes.map(type => (
                      <SelectItem key={type.value} value={type.value}>
                        <div className="flex items-center gap-2">
                          <type.icon className="w-4 h-4" />
                          {type.label}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Label htmlFor="scenario-description">Description</Label>
              <Textarea
                id="scenario-description"
                value={newScenario.description}
                onChange={(e) => setNewScenario(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Describe the scenario..."
                rows={3}
              />
            </div>

            {/* Environmental Conditions */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>Weather</Label>
                <Select
                  value={newScenario.environmentalConditions.weather}
                  onValueChange={(value) => setNewScenario(prev => ({
                    ...prev,
                    environmentalConditions: { ...prev.environmentalConditions, weather: value }
                  }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {weatherConditions.map(condition => (
                      <SelectItem key={condition.value} value={condition.value}>
                        {condition.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Lighting</Label>
                <Select
                  value={newScenario.environmentalConditions.lighting}
                  onValueChange={(value) => setNewScenario(prev => ({
                    ...prev,
                    environmentalConditions: { ...prev.environmentalConditions, lighting: value }
                  }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {lightingConditions.map(condition => (
                      <SelectItem key={condition.value} value={condition.value}>
                        {condition.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="visibility">Visibility (m)</Label>
                <Input
                  id="visibility"
                  type="number"
                  value={newScenario.environmentalConditions.visibility}
                  onChange={(e) => setNewScenario(prev => ({
                    ...prev,
                    environmentalConditions: { ...prev.environmentalConditions, visibility: parseInt(e.target.value) }
                  }))}
                  min="100"
                  max="50000"
                />
              </div>
            </div>

            {/* Object Management */}
            <div className="space-y-4">
              <h4 className="font-medium">Detection Objects</h4>

              {/* Add Object Form */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                <div>
                  <Label>Object Type</Label>
                  <Select
                    value={newObject.type}
                    onValueChange={(value: ScenarioObject['type']) => setNewObject(prev => ({ ...prev, type: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {objectTypes.map(type => (
                        <SelectItem key={type.value} value={type.value}>
                          <div className="flex items-center gap-2">
                            <type.icon className="w-4 h-4" />
                            {type.label}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Latitude</Label>
                  <Input
                    type="number"
                    step="0.000001"
                    value={newObject.latitude}
                    onChange={(e) => setNewObject(prev => ({ ...prev, latitude: parseFloat(e.target.value) }))}
                  />
                </div>
                <div>
                  <Label>Longitude</Label>
                  <Input
                    type="number"
                    step="0.000001"
                    value={newObject.longitude}
                    onChange={(e) => setNewObject(prev => ({ ...prev, longitude: parseFloat(e.target.value) }))}
                  />
                </div>
                <div className="flex items-end">
                  <Button onClick={handleAddObject} className="w-full">
                    <Plus className="w-4 h-4 mr-2" />
                    Add
                  </Button>
                </div>
              </div>

              {/* Object List */}
              {newScenario.objects.length > 0 && (
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {newScenario.objects.map(obj => (
                    <div key={obj.id} className="flex items-center justify-between p-2 border rounded">
                      <div className="flex items-center gap-2">
                        {getObjectIcon(obj.type)}
                        <span className="text-sm">
                          {obj.type} at ({obj.latitude.toFixed(6)}, {obj.longitude.toFixed(6)})
                        </span>
                        {obj.mobile && <Badge variant="outline" className="text-xs">Mobile</Badge>}
                      </div>
                      <Button
                        onClick={() => handleRemoveObject(obj.id)}
                        variant="outline"
                        size="sm"
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex gap-2">
              <Button onClick={handleCreateScenario} className="flex-1">
                <CheckCircle className="w-4 h-4 mr-2" />
                Create Scenario
              </Button>
              <Button
                onClick={() => setShowCreateForm(false)}
                variant="outline"
                className="flex-1"
              >
                Cancel
              </Button>
            </div>
          </div>
        )}

        {scenarios.length === 0 && !showCreateForm && (
          <Alert>
            <AlertTriangle className="w-4 h-4" />
            <AlertDescription>
              No scenarios available. Create your first scenario to begin testing.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default ScenarioManager;