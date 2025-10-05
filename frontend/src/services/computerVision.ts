import api from './api'

export interface Detection {
  class_name: string
  confidence: number
  bounding_box: {
    x1: number
    y1: number
    x2: number
    y2: number
    width: number
    height: number
    center_x: number
    center_y: number
  }
  priority: 'low' | 'medium' | 'high' | 'critical'
  timestamp: string
  model_used: string
  image_size: {
    width: number
    height: number
  }
  mission_context?: {
    mission_id?: string
    search_target?: string
    priority_boost: number
  }
}

export interface ImageQualityAnalysis {
  quality_score: number
  issues: string[]
  metrics: {
    brightness: number
    contrast: number
    sharpness: number
    noise_level: number
    resolution: string
  }
}

export interface ModelInfo {
  available: boolean
  models: Record<string, {
    available: boolean
    classes: number
    class_names: string[]
  }>
  sar_classes?: Record<string, {
    priority: string
    confidence_threshold: number
  }>
  detection_threshold?: number
  message?: string
}

export interface OptimizedSettings {
  confidence_threshold: number
  accuracy_score: number
  recommendations: string[]
}

export const computerVisionService = {
  /**
   * Detect objects in an uploaded image
   */
  async detectObjects(
    image: File,
    options?: {
      modelSize?: 'yolov8n' | 'yolov8s' | 'yolov8m' | 'yolov8l'
      confidenceThreshold?: number
      targetClasses?: string[]
    }
  ) {
    const formData = new FormData()
    formData.append('image', image)
    
    if (options?.modelSize) {
      formData.append('model_size', options.modelSize)
    }
    
    if (options?.confidenceThreshold !== undefined) {
      formData.append('confidence_threshold', options.confidenceThreshold.toString())
    }
    
    if (options?.targetClasses) {
      formData.append('target_classes', JSON.stringify(options.targetClasses))
    }

    const response = await api.post('/computer-vision/detect-objects', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * Detect SAR-specific targets with mission context
   */
  async detectSarTargets(
    image: File,
    missionContext?: {
      missionId?: string
      searchTarget?: string
    }
  ) {
    const formData = new FormData()
    formData.append('image', image)
    
    if (missionContext?.missionId) {
      formData.append('mission_id', missionContext.missionId)
    }
    
    if (missionContext?.searchTarget) {
      formData.append('search_target', missionContext.searchTarget)
    }

    const response = await api.post('/computer-vision/detect-sar-targets', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * Analyze image quality for detection optimization
   */
  async analyzeImageQuality(image: File) {
    const formData = new FormData()
    formData.append('image', image)

    const response = await api.post('/computer-vision/analyze-image-quality', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * Process a batch of images for object detection
   */
  async batchDetectObjects(
    images: File[],
    modelSize: 'yolov8n' | 'yolov8s' | 'yolov8m' | 'yolov8l' = 'yolov8s'
  ) {
    const formData = new FormData()
    
    images.forEach(image => {
      formData.append('images', image)
    })
    
    formData.append('model_size', modelSize)

    const response = await api.post('/computer-vision/batch-detect', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * Get information about available computer vision models
   */
  async getModelInfo(): Promise<{ success: boolean; model_info: ModelInfo }> {
    const response = await api.get('/computer-vision/model-info')
    return response.data
  },

  /**
   * Optimize detection settings based on sample images
   */
  async optimizeSettings(
    images: File[],
    targetAccuracy: number = 0.8
  ) {
    const formData = new FormData()
    
    images.forEach(image => {
      formData.append('images', image)
    })
    
    formData.append('target_accuracy', targetAccuracy.toString())

    const response = await api.post('/computer-vision/optimize-settings', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * Get SAR-specific object classes and their priorities
   */
  async getSarClasses() {
    const response = await api.get('/computer-vision/sar-classes')
    return response.data
  },

  /**
   * Test endpoint for computer vision functionality
   */
  async testDetection(image: File) {
    const formData = new FormData()
    formData.append('image', image)

    const response = await api.post('/computer-vision/test-detection', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  /**
   * Utility function to convert image file to base64
   */
  async imageToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => {
        const result = reader.result as string
        // Remove data URL prefix
        const base64 = result.split(',')[1]
        resolve(base64)
      }
      reader.onerror = reject
      reader.readAsDataURL(file)
    })
  },

  /**
   * Utility function to create a preview URL from file
   */
  createPreviewUrl(file: File): string {
    return URL.createObjectURL(file)
  },

  /**
   * Utility function to validate image file
   */
  validateImageFile(file: File): { valid: boolean; error?: string } {
    // Check file type
    if (!file.type.startsWith('image/')) {
      return { valid: false, error: 'File must be an image' }
    }

    // Check file size (10MB limit)
    const maxSize = 10 * 1024 * 1024
    if (file.size > maxSize) {
      return { valid: false, error: 'File size must be less than 10MB' }
    }

    return { valid: true }
  },

  /**
   * Utility function to get priority color
   */
  getPriorityColor(priority: string): string {
    switch (priority) {
      case 'critical': return 'text-red-600 bg-red-100'
      case 'high': return 'text-orange-600 bg-orange-100'
      case 'medium': return 'text-yellow-600 bg-yellow-100'
      case 'low': return 'text-green-600 bg-green-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  },

  /**
   * Utility function to get priority icon
   */
  getPriorityIcon(priority: string): string {
    switch (priority) {
      case 'critical': return '🚨'
      case 'high': return '⚠️'
      case 'medium': return '⚡'
      case 'low': return 'ℹ️'
      default: return '📢'
    }
  },

  /**
   * Utility function to format confidence score
   */
  formatConfidence(confidence: number): string {
    return `${(confidence * 100).toFixed(1)}%`
  },

  /**
   * Utility function to get quality score color
   */
  getQualityScoreColor(score: number): string {
    if (score >= 0.8) return 'text-green-600'
    if (score >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }
}
