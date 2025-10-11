import React, { useState, useRef, useCallback } from 'react'
import { computerVisionService, Detection, ImageQualityAnalysis, ModelInfo } from '../../services/computerVision'

interface ComputerVisionProps {
  onDetectionComplete?: (detections: Detection[]) => void
  missionContext?: {
    missionId?: string
    searchTarget?: string
  }
  className?: string
}

const ComputerVision: React.FC<ComputerVisionProps> = ({
  onDetectionComplete,
  missionContext,
  className = ''
}) => {
  const [isLoading, setIsLoading] = useState(false)
  const [selectedImage, setSelectedImage] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [detections, setDetections] = useState<Detection[]>([])
  const [qualityAnalysis, setQualityAnalysis] = useState<ImageQualityAnalysis | null>(null)
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'detection' | 'quality' | 'models'>('detection')
  
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleImageSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file
    const validation = computerVisionService.validateImageFile(file)
    if (!validation.valid) {
      setError(validation.error || 'Invalid file')
      return
    }

    setSelectedImage(file)
    setError(null)
    setDetections([])
    setQualityAnalysis(null)

    // Create preview
    const previewUrl = computerVisionService.createPreviewUrl(file)
    setImagePreview(previewUrl)
  }, [])

  const handleDetectObjects = useCallback(async () => {
    if (!selectedImage) return

    try {
      setIsLoading(true)
      setError(null)

      const response = await computerVisionService.detectObjects(selectedImage, {
        modelSize: 'yolov8s',
        confidenceThreshold: 0.6
      })

      if (response.success) {
        setDetections(response.detections)
        if (onDetectionComplete) {
          onDetectionComplete(response.detections)
        }
      } else {
        setError('Detection failed')
      }
    } catch (error) {
      console.error('Detection error:', error)
      setError('Failed to detect objects. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }, [selectedImage, onDetectionComplete])

  const handleDetectSarTargets = useCallback(async () => {
    if (!selectedImage) return

    try {
      setIsLoading(true)
      setError(null)

      const response = await computerVisionService.detectSarTargets(selectedImage, missionContext)

      if (response.success) {
        setDetections(response.detections)
        if (onDetectionComplete) {
          onDetectionComplete(response.detections)
        }
      } else {
        setError('SAR target detection failed')
      }
    } catch (error) {
      console.error('SAR detection error:', error)
      setError('Failed to detect SAR targets. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }, [selectedImage, missionContext, onDetectionComplete])

  const handleAnalyzeQuality = useCallback(async () => {
    if (!selectedImage) return

    try {
      setIsLoading(true)
      setError(null)

      const response = await computerVisionService.analyzeImageQuality(selectedImage)

      if (response.success) {
        setQualityAnalysis(response.quality_analysis)
      } else {
        setError('Quality analysis failed')
      }
    } catch (error) {
      console.error('Quality analysis error:', error)
      setError('Failed to analyze image quality. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }, [selectedImage])

  const loadModelInfo = useCallback(async () => {
    try {
      const response = await computerVisionService.getModelInfo()
      if (response.success) {
        setModelInfo(response.model_info)
      }
    } catch (error) {
      console.error('Failed to load model info:', error)
    }
  }, [])

  const clearImage = useCallback(() => {
    setSelectedImage(null)
    setImagePreview(null)
    setDetections([])
    setQualityAnalysis(null)
    setError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }, [])

  const getPriorityColor = (priority: string) => {
    return computerVisionService.getPriorityColor(priority)
  }

  const getPriorityIcon = (priority: string) => {
    return computerVisionService.getPriorityIcon(priority)
  }

  const formatConfidence = (confidence: number) => {
    return computerVisionService.formatConfidence(confidence)
  }

  const getQualityScoreColor = (score: number) => {
    return computerVisionService.getQualityScoreColor(score)
  }

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Computer Vision Analysis</h2>
        <p className="text-sm text-gray-600">Upload an image for object detection and analysis</p>
      </div>

      {/* Image Upload */}
      <div className="mb-6">
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
          {!selectedImage ? (
            <div>
              <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <div className="mt-4">
                <label htmlFor="image-upload" className="cursor-pointer">
                  <span className="mt-2 block text-sm font-medium text-gray-900">
                    Upload an image
                  </span>
                  <span className="mt-1 block text-sm text-gray-500">
                    PNG, JPG, GIF up to 10MB
                  </span>
                </label>
                <input
                  ref={fileInputRef}
                  id="image-upload"
                  type="file"
                  accept="image/*"
                  onChange={handleImageSelect}
                  className="sr-only"
                />
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="relative">
                <img
                  src={imagePreview || ''}
                  alt="Uploaded"
                  className="mx-auto max-h-64 rounded-lg"
                />
                <button
                  onClick={clearImage}
                  className="absolute top-2 right-2 bg-red-600 hover:bg-red-700 text-white rounded-full p-1"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="text-sm text-gray-600">
                <p><strong>File:</strong> {selectedImage.name}</p>
                <p><strong>Size:</strong> {(selectedImage.size / 1024 / 1024).toFixed(2)} MB</p>
                <p><strong>Type:</strong> {selectedImage.type}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4 text-red-800">
          <p>{error}</p>
        </div>
      )}

      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('detection')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'detection'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Object Detection
            </button>
            <button
              onClick={() => setActiveTab('quality')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'quality'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Quality Analysis
            </button>
            <button
              onClick={() => {
                setActiveTab('models')
                loadModelInfo()
              }}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'models'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Model Info
            </button>
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'detection' && (
        <div className="space-y-4">
          <div className="flex space-x-3">
            <button
              onClick={handleDetectObjects}
              disabled={!selectedImage || isLoading}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-md font-medium"
            >
              {isLoading ? 'Detecting...' : 'Detect Objects'}
            </button>
            <button
              onClick={handleDetectSarTargets}
              disabled={!selectedImage || isLoading}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-md font-medium"
            >
              {isLoading ? 'Detecting...' : 'Detect SAR Targets'}
            </button>
          </div>

          {detections.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-md font-semibold text-gray-900">
                Detections ({detections.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {detections.map((detection, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="text-lg">{getPriorityIcon(detection.priority)}</span>
                        <span className="font-medium text-gray-900 capitalize">
                          {detection.class_name}
                        </span>
                      </div>
                      <span className={`px-2 py-1 text-xs rounded-full ${getPriorityColor(detection.priority)}`}>
                        {detection.priority}
                      </span>
                    </div>
                    <div className="text-sm text-gray-600 space-y-1">
                      <p><strong>Confidence:</strong> {formatConfidence(detection.confidence)}</p>
                      <p><strong>Model:</strong> {detection.model_used}</p>
                      <p><strong>Position:</strong> ({detection.bounding_box.center_x.toFixed(0)}, {detection.bounding_box.center_y.toFixed(0)})</p>
                      <p><strong>Size:</strong> {detection.bounding_box.width.toFixed(0)} × {detection.bounding_box.height.toFixed(0)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'quality' && (
        <div className="space-y-4">
          <button
            onClick={handleAnalyzeQuality}
            disabled={!selectedImage || isLoading}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white rounded-md font-medium"
          >
            {isLoading ? 'Analyzing...' : 'Analyze Image Quality'}
          </button>

          {qualityAnalysis && (
            <div className="space-y-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-md font-semibold text-gray-900 mb-3">Quality Analysis</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Overall Quality Score</p>
                    <p className={`text-2xl font-bold ${getQualityScoreColor(qualityAnalysis.quality_score)}`}>
                      {(qualityAnalysis.quality_score * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Issues Detected</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {qualityAnalysis.issues.length}
                    </p>
                  </div>
                </div>
              </div>

              {qualityAnalysis.issues.length > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <h4 className="text-sm font-semibold text-yellow-800 mb-2">Issues Found</h4>
                  <ul className="text-sm text-yellow-700 space-y-1">
                    {qualityAnalysis.issues.map((issue, index) => (
                      <li key={index}>• {issue}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-gray-900 mb-3">Detailed Metrics</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600">Brightness</p>
                    <p className="font-medium">{qualityAnalysis.metrics.brightness}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Contrast</p>
                    <p className="font-medium">{qualityAnalysis.metrics.contrast}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Sharpness</p>
                    <p className="font-medium">{qualityAnalysis.metrics.sharpness}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Noise Level</p>
                    <p className="font-medium">{qualityAnalysis.metrics.noise_level}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Resolution</p>
                    <p className="font-medium">{qualityAnalysis.metrics.resolution}</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'models' && (
        <div className="space-y-4">
          {modelInfo ? (
            <div className="space-y-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-md font-semibold text-gray-900 mb-3">Model Status</h3>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    modelInfo.available ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {modelInfo.available ? 'Available' : 'Not Available'}
                  </span>
                  {modelInfo.message && (
                    <span className="text-sm text-gray-600">{modelInfo.message}</span>
                  )}
                </div>
              </div>

              {modelInfo.available && (
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-gray-900">Available Models</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {Object.entries(modelInfo.models).map(([name, info]) => (
                      <div key={name} className="border border-gray-200 rounded-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-gray-900">{name}</span>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            info.available ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {info.available ? 'Ready' : 'Not Ready'}
                          </span>
                        </div>
                        <div className="text-sm text-gray-600">
                          <p><strong>Classes:</strong> {info.classes}</p>
                          <p><strong>Class Names:</strong> {info.class_names.slice(0, 3).join(', ')}...</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {modelInfo.sar_classes && (
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-gray-900">SAR Classes</h4>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-600 mb-2">
                      Total SAR-specific classes: {Object.keys(modelInfo.sar_classes).length}
                    </p>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
                      {Object.entries(modelInfo.sar_classes).slice(0, 12).map(([name, config]) => (
                        <div key={name} className="flex items-center justify-between">
                          <span className="capitalize">{name}</span>
                          <span className={`px-1 py-0.5 rounded text-xs ${getPriorityColor(config.priority)}`}>
                            {config.priority}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center text-gray-500 py-8">
              <p>Click "Model Info" tab to load model information</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default ComputerVision
