/**
 * Caching utilities for API responses and application data.
 */

import { useState, useCallback, useEffect } from 'react';

interface CacheEntry<T> {
  data: T
  timestamp: number
  ttl: number // Time to live in milliseconds
}

interface CacheOptions {
  ttl?: number // Default: 5 minutes
  key?: string
}

class CacheManager {
  private cache = new Map<string, CacheEntry<any>>()
  private defaultTTL = 5 * 60 * 1000 // 5 minutes

  set<T>(key: string, data: T, options: CacheOptions = {}): void {
    const { ttl = this.defaultTTL } = options

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    })
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key)

    if (!entry) {
      return null
    }

    // Check if entry has expired
    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key)
      return null
    }

    return entry.data
  }

  has(key: string): boolean {
    const entry = this.cache.get(key)
    if (!entry) return false

    // Check if entry has expired
    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key)
      return false
    }

    return true
  }

  delete(key: string): boolean {
    return this.cache.delete(key)
  }

  clear(): void {
    this.cache.clear()
  }

  // Clean up expired entries
  cleanup(): void {
    const now = Date.now()
    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > entry.ttl) {
        this.cache.delete(key)
      }
    }
  }

  // Get all keys
  keys(): string[] {
    return Array.from(this.cache.keys())
  }

  // Get cache size
  size(): number {
    this.cleanup() // Clean up before returning size
    return this.cache.size
  }

  // Generate cache key from parameters
  generateKey(baseKey: string, params?: Record<string, any>): string {
    if (!params) return baseKey

    const sortedParams = Object.keys(params)
      .sort()
      .map(key => `${key}:${params[key]}`)
      .join('|')

    return `${baseKey}:${sortedParams}`
  }
}

// Global cache instance
export const cache = new CacheManager()

// React hook for caching data
export function useCache<T>(
  key: string,
  fetcher: () => Promise<T>,
  options: CacheOptions = {}
): {
  data: T | null
  loading: boolean
  error: Error | null
  refetch: () => Promise<void>
} {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      // Check cache first
      const cachedData = cache.get<T>(key)
      if (cachedData !== null) {
        setData(cachedData)
        setLoading(false)
        return
      }

      // Fetch fresh data
      const freshData = await fetcher()
      setData(freshData)

      // Cache the result
      cache.set(key, freshData, options)

    } catch (err) {
      setError(err instanceof Error ? err : new Error('An error occurred'))
    } finally {
      setLoading(false)
    }
  }, [key, fetcher, options.ttl])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return {
    data,
    loading,
    error,
    refetch: fetchData
  }
}

// Cache decorator for functions
export function withCache<T extends (...args: any[]) => Promise<any>>(
  fn: T,
  options: CacheOptions & { generateKey?: (args: Parameters<T>) => string } = {}
): T {
  const { ttl = 5 * 60 * 1000, generateKey } = options

  return (async (...args: Parameters<T>) => {
    const cacheKey = generateKey ? generateKey(args) : cache.generateKey(fn.name, { args })

    // Check cache first
    const cached = cache.get<ReturnType<T>>(cacheKey)
    if (cached !== null) {
      return cached
    }

    // Execute function and cache result
    const result = await fn(...args)
    cache.set(cacheKey, result, { ttl })

    return result
  }) as T
}

// IndexedDB cache for larger data (fallback for localStorage)
class IndexedDBCache {
  private dbName = 'SARDroneCache'
  private dbVersion = 1
  private db: IDBDatabase | null = null

  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion)

      request.onerror = () => reject(request.error)
      request.onsuccess = () => {
        this.db = request.result
        resolve()
      }

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result
        if (!db.objectStoreNames.contains('cache')) {
          db.createObjectStore('cache', { keyPath: 'key' })
        }
      }
    })
  }

  async set<T>(key: string, data: T, ttl: number = 5 * 60 * 1000): Promise<void> {
    if (!this.db) await this.init()

    const entry = {
      key,
      data,
      timestamp: Date.now(),
      ttl
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['cache'], 'readwrite')
      const store = transaction.objectStore('cache')
      const request = store.put(entry)

      request.onerror = () => reject(request.error)
      request.onsuccess = () => resolve()
    })
  }

  async get<T>(key: string): Promise<T | null> {
    if (!this.db) await this.init()

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['cache'], 'readonly')
      const store = transaction.objectStore('cache')
      const request = store.get(key)

      request.onerror = () => reject(request.error)
      request.onsuccess = () => {
        const entry = request.result
        if (!entry) {
          resolve(null)
          return
        }

        // Check if expired
        if (Date.now() - entry.timestamp > entry.ttl) {
          // Clean up expired entry
          const deleteTransaction = this.db!.transaction(['cache'], 'readwrite')
          const deleteStore = deleteTransaction.objectStore('cache')
          deleteStore.delete(key)
          resolve(null)
          return
        }

        resolve(entry.data)
      }
    })
  }
}

// IndexedDB cache instance for large data
export const persistentCache = new IndexedDBCache()

export default cache
