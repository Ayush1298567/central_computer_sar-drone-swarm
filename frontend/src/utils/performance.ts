/**
 * Performance monitoring utilities for the SAR Drone application.
 */

import { useEffect } from 'react';

interface PerformanceMetric {
  name: string
  value: number
  timestamp: number
  category: 'navigation' | 'paint' | 'resource' | 'custom'
}

class PerformanceMonitor {
  private metrics: PerformanceMetric[] = []
  private observers: PerformanceObserver[] = []

  constructor() {
    this.initializeObservers()
    this.trackInitialLoad()
  }

  private initializeObservers() {
    // Navigation timing
    if ('performance' in window && 'observe' in window.PerformanceObserver.prototype) {
      try {
        const navigationObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.entryType === 'navigation') {
              this.recordMetric({
                name: 'navigation-timing',
                value: entry.duration,
                timestamp: Date.now(),
                category: 'navigation'
              })
            }
          }
        })
        navigationObserver.observe({ entryTypes: ['navigation'] })
        this.observers.push(navigationObserver)

        // Paint timing
        const paintObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            this.recordMetric({
              name: entry.name,
              value: entry.startTime,
              timestamp: Date.now(),
              category: 'paint'
            })
          }
        })
        paintObserver.observe({ entryTypes: ['paint'] })
        this.observers.push(paintObserver)

        // Resource timing
        const resourceObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.duration > 0) {
              this.recordMetric({
                name: `resource-${entry.name}`,
                value: entry.duration,
                timestamp: Date.now(),
                category: 'resource'
              })
            }
          }
        })
        resourceObserver.observe({ entryTypes: ['resource'] })
        this.observers.push(resourceObserver)

      } catch (error) {
        console.warn('Performance monitoring not fully supported:', error)
      }
    }
  }

  private trackInitialLoad() {
    // Track initial page load
    window.addEventListener('load', () => {
      setTimeout(() => {
        const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
        if (navigation) {
          this.recordMetric({
            name: 'page-load-time',
            value: navigation.loadEventEnd - navigation.fetchStart,
            timestamp: Date.now(),
            category: 'navigation'
          })

          this.recordMetric({
            name: 'dom-ready-time',
            value: navigation.domContentLoadedEventEnd - navigation.fetchStart,
            timestamp: Date.now(),
            category: 'navigation'
          })
        }
      }, 0)
    })
  }

  recordMetric(metric: PerformanceMetric) {
    this.metrics.push(metric)

    // Keep only last 1000 metrics to prevent memory issues
    if (this.metrics.length > 1000) {
      this.metrics = this.metrics.slice(-1000)
    }

    // Send to analytics service in production
    if (process.env.NODE_ENV === 'production') {
      this.sendToAnalytics(metric)
    }

    // Log in development
    if (process.env.NODE_ENV === 'development') {
      console.log('Performance Metric:', metric)
    }
  }

  recordCustomMetric(name: string, value: number) {
    this.recordMetric({
      name,
      value,
      timestamp: Date.now(),
      category: 'custom'
    })
  }

  private sendToAnalytics(metric: PerformanceMetric) {
    // In a real application, you would send this to your analytics service
    // For now, we'll just store it locally
    try {
      const existingMetrics = JSON.parse(localStorage.getItem('performance-metrics') || '[]')
      existingMetrics.push(metric)

      // Keep only last 100 metrics in localStorage
      if (existingMetrics.length > 100) {
        existingMetrics.splice(0, existingMetrics.length - 100)
      }

      localStorage.setItem('performance-metrics', JSON.stringify(existingMetrics))
    } catch (error) {
      console.warn('Failed to store performance metrics:', error)
    }
  }

  getMetrics(category?: PerformanceMetric['category']) {
    if (category) {
      return this.metrics.filter(metric => metric.category === category)
    }
    return [...this.metrics]
  }

  getAverageMetric(name: string): number | null {
    const metrics = this.metrics.filter(metric => metric.name === name)
    if (metrics.length === 0) return null

    const sum = metrics.reduce((acc, metric) => acc + metric.value, 0)
    return sum / metrics.length
  }

  getSlowestResources(limit: number = 10): PerformanceMetric[] {
    return this.metrics
      .filter(metric => metric.category === 'resource')
      .sort((a, b) => b.value - a.value)
      .slice(0, limit)
  }

  generateReport(): {
    totalMetrics: number
    categories: Record<string, number>
    slowestResources: PerformanceMetric[]
    averageLoadTime: number | null
    averagePaintTime: number | null
  } {
    const categories = this.metrics.reduce((acc, metric) => {
      acc[metric.category] = (acc[metric.category] || 0) + 1
      return acc
    }, {} as Record<string, number>)

    return {
      totalMetrics: this.metrics.length,
      categories,
      slowestResources: this.getSlowestResources(),
      averageLoadTime: this.getAverageMetric('page-load-time'),
      averagePaintTime: this.getAverageMetric('first-contentful-paint')
    }
  }

  destroy() {
    this.observers.forEach(observer => observer.disconnect())
    this.observers = []
    this.metrics = []
  }
}

// Global performance monitor instance
export const performanceMonitor = new PerformanceMonitor()

// React hook for measuring component render performance
export function usePerformanceMeasurement(componentName: string) {
  const startTime = performance.now()

  useEffect(() => {
    const endTime = performance.now()
    const renderTime = endTime - startTime

    performanceMonitor.recordCustomMetric(
      `component-render-${componentName}`,
      renderTime
    )
  })

  return {
    recordMetric: (name: string, value: number) => {
      performanceMonitor.recordCustomMetric(`${componentName}-${name}`, value)
    }
  }
}

// Utility for measuring async operations
export async function measureAsyncOperation<T>(
  operationName: string,
  operation: () => Promise<T>
): Promise<T> {
  const startTime = performance.now()
  try {
    const result = await operation()
    const duration = performance.now() - startTime
    performanceMonitor.recordCustomMetric(`async-${operationName}`, duration)
    return result
  } catch (error) {
    const duration = performance.now() - startTime
    performanceMonitor.recordCustomMetric(`async-${operationName}-error`, duration)
    throw error
  }
}

export default performanceMonitor
