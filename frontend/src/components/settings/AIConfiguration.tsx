import React, { useState, useEffect } from 'react';
import { Brain, Key, Server, Settings, Save, RefreshCw, Eye, EyeOff } from 'lucide-react';
import { AIConfiguration as AIConfigurationType } from '../../types';
import { apiService } from '../../utils/api';

interface AIConfigurationProps {
  onClose?: () => void;
}

const AIConfiguration: React.FC<AIConfigurationProps> = ({ onClose }) => {
  const [config, setConfig] = useState<AIConfigurationType>({
    provider: 'ollama',
    model: 'llama3.2:3b',
    api_key: '',
    base_url: 'http://localhost:11434',
    timeout: 30,
    temperature: 0.1,
    max_tokens: 1000,
  });

  const [originalConfig, setOriginalConfig] = useState<AIConfigurationType>(config);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  useEffect(() => {
    loadConfiguration();
  }, []);

  useEffect(() => {
    // Check for unsaved changes
    const changed = JSON.stringify(config) !== JSON.stringify(originalConfig);
    setHasUnsavedChanges(changed);
  }, [config, originalConfig]);

  const loadConfiguration = async () => {
    setIsLoading(true);
    try {
      const aiConfig = await apiService.getAIConfiguration();
      setConfig(aiConfig);
      setOriginalConfig(aiConfig);
    } catch (error) {
      console.error('Failed to load AI configuration:', error);
      // Keep default configuration
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const result = await apiService.updateAIConfiguration(config);
      if (result.success) {
        setOriginalConfig(config);
        setHasUnsavedChanges(false);
        alert('AI configuration saved successfully');
      } else {
        alert('Failed to save AI configuration');
      }
    } catch (error) {
      console.error('Failed to save AI configuration:', error);
      alert('Failed to save AI configuration');
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    if (confirm('Are you sure you want to reset the AI configuration to defaults?')) {
      setConfig(originalConfig);
    }
  };

  const testConnection = async () => {
    setIsTesting(true);
    setTestResult(null);

    try {
      // Test the AI service connection
      const response = await fetch(`${config.base_url}/api/tags`);
      const data = await response.json();

      if (response.ok) {
        const hasModel = data.models?.some((model: any) => model.name === config.model);
        setTestResult({
          success: hasModel,
          message: hasModel
            ? `Successfully connected to ${config.provider}. Model "${config.model}" is available.`
            : `Connected to ${config.provider}, but model "${config.model}" is not available.`
        });
      } else {
        setTestResult({
          success: false,
          message: `Failed to connect to ${config.provider} at ${config.base_url}`
        });
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: `Connection failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      });
    } finally {
      setIsTesting(false);
    }
  };

  const updateConfig = <K extends keyof AIConfigurationType>(key: K, value: AIConfigurationType[K]) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  if (isLoading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-2 text-gray-600">Loading AI configuration...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Brain className="h-6 w-6 text-purple-600 mr-2" />
          <h2 className="text-xl font-bold text-gray-800">AI Configuration</h2>
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

      {/* AI Provider Selection */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">AI Provider</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <label className="flex items-center">
            <input
              type="radio"
              name="provider"
              value="ollama"
              checked={config.provider === 'ollama'}
              onChange={(e) => updateConfig('provider', e.target.value as AIConfigurationType['provider'])}
              className="mr-3"
            />
            <div>
              <span className="font-medium text-gray-800">Ollama (Local)</span>
              <p className="text-xs text-gray-600">Run AI models locally</p>
            </div>
          </label>
          <label className="flex items-center">
            <input
              type="radio"
              name="provider"
              value="openai"
              checked={config.provider === 'openai'}
              onChange={(e) => updateConfig('provider', e.target.value as AIConfigurationType['provider'])}
              className="mr-3"
            />
            <div>
              <span className="font-medium text-gray-800">OpenAI</span>
              <p className="text-xs text-gray-600">GPT models via API</p>
            </div>
          </label>
          <label className="flex items-center">
            <input
              type="radio"
              name="provider"
              value="anthropic"
              checked={config.provider === 'anthropic'}
              onChange={(e) => updateConfig('provider', e.target.value as AIConfigurationType['provider'])}
              className="mr-3"
            />
            <div>
              <span className="font-medium text-gray-800">Anthropic</span>
              <p className="text-xs text-gray-600">Claude models via API</p>
            </div>
          </label>
        </div>
      </div>

      {/* Provider-specific Configuration */}
      <div className="space-y-6">
        {/* Ollama Configuration */}
        {config.provider === 'ollama' && (
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Ollama Configuration</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Base URL
                </label>
                <input
                  type="url"
                  value={config.base_url}
                  onChange={(e) => updateConfig('base_url', e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                  placeholder="http://localhost:11434"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Model Name
                </label>
                <select
                  value={config.model}
                  onChange={(e) => updateConfig('model', e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                >
                  <option value="llama3.2:3b">Llama 3.2 3B</option>
                  <option value="llama3.2:1b">Llama 3.2 1B</option>
                  <option value="llama3.1:8b">Llama 3.1 8B</option>
                  <option value="mistral:7b">Mistral 7B</option>
                  <option value="codellama:7b">Code Llama 7B</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* OpenAI Configuration */}
        {config.provider === 'openai' && (
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-4">OpenAI Configuration</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API Key
                </label>
                <div className="relative">
                  <input
                    type={showApiKey ? 'text' : 'password'}
                    value={config.api_key}
                    onChange={(e) => updateConfig('api_key', e.target.value)}
                    className="w-full p-3 pr-10 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    placeholder="sk-..."
                  />
                  <button
                    type="button"
                    onClick={() => setShowApiKey(!showApiKey)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Model
                </label>
                <select
                  value={config.model}
                  onChange={(e) => updateConfig('model', e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                >
                  <option value="gpt-4">GPT-4</option>
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                  <option value="gpt-4-turbo">GPT-4 Turbo</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Anthropic Configuration */}
        {config.provider === 'anthropic' && (
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Anthropic Configuration</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API Key
                </label>
                <div className="relative">
                  <input
                    type={showApiKey ? 'text' : 'password'}
                    value={config.api_key}
                    onChange={(e) => updateConfig('api_key', e.target.value)}
                    className="w-full p-3 pr-10 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                    placeholder="sk-ant-api03-..."
                  />
                  <button
                    type="button"
                    onClick={() => setShowApiKey(!showApiKey)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Model
                </label>
                <select
                  value={config.model}
                  onChange={(e) => updateConfig('model', e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
                >
                  <option value="claude-3-opus">Claude 3 Opus</option>
                  <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                  <option value="claude-3-haiku">Claude 3 Haiku</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Advanced Settings */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Advanced Settings</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Request Timeout (seconds)
              </label>
              <input
                type="number"
                min="10"
                max="300"
                value={config.timeout}
                onChange={(e) => updateConfig('timeout', parseInt(e.target.value))}
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Temperature
              </label>
              <input
                type="number"
                min="0"
                max="2"
                step="0.1"
                value={config.temperature}
                onChange={(e) => updateConfig('temperature', parseFloat(e.target.value))}
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Tokens
              </label>
              <input
                type="number"
                min="100"
                max="4000"
                value={config.max_tokens}
                onChange={(e) => updateConfig('max_tokens', parseInt(e.target.value))}
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
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
                <p className="text-sm font-medium text-gray-700">
                  {config.provider.charAt(0).toUpperCase() + config.provider.slice(1)} Connection
                </p>
                <p className="text-xs text-gray-500">
                  Test connection to {config.provider} service
                </p>
              </div>
              <button
                onClick={testConnection}
                disabled={isTesting}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-md text-sm font-medium flex items-center"
              >
                {isTesting ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Testing...
                  </>
                ) : (
                  <>
                    <Server className="h-4 w-4 mr-2" />
                    Test Connection
                  </>
                )}
              </button>
            </div>

            {testResult && (
              <div className={`mt-4 p-3 rounded-md ${testResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                <div className="flex items-center">
                  {testResult.success ? (
                    <Settings className="h-5 w-5 text-green-600 mr-2" />
                  ) : (
                    <Settings className="h-5 w-5 text-red-600 mr-2" />
                  )}
                  <span className={`text-sm font-medium ${testResult.success ? 'text-green-800' : 'text-red-800'}`}>
                    {testResult.message}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Configuration Summary */}
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <h4 className="font-medium text-purple-800 mb-2">AI Configuration Summary</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-purple-600 font-medium">Provider:</span>
              <p className="text-purple-700 capitalize">{config.provider}</p>
            </div>
            <div>
              <span className="text-purple-600 font-medium">Model:</span>
              <p className="text-purple-700">{config.model}</p>
            </div>
            <div>
              <span className="text-purple-600 font-medium">Timeout:</span>
              <p className="text-purple-700">{config.timeout}s</p>
            </div>
            <div>
              <span className="text-purple-600 font-medium">Temperature:</span>
              <p className="text-purple-700">{config.temperature}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIConfiguration;
