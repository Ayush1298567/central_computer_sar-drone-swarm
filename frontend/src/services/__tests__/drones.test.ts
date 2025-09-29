import { describe, it, expect, vi, beforeEach } from 'vitest'
import { droneService } from '../drones'
import api from '../api'

// Mock the API
vi.mock('../api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  }
}))

const mockedApi = vi.mocked(api)

describe('Drone Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const mockDrone = {
    id: '1',
    drone_id: 'test-drone-1',
    name: 'Test Drone',
    status: 'online',
    battery_level: 85,
    position_lat: 40.7128,
    position_lng: -74.0060,
    position_alt: 30,
    heading: 0,
    speed: 0,
    last_seen: '2024-01-01T00:00:00Z',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  }

  describe('getDrones', () => {
    it('should fetch drones with default parameters', async () => {
      const mockResponse = { data: [mockDrone] }
      mockedApi.get.mockResolvedValue(mockResponse)

      const result = await droneService.getDrones()

      expect(mockedApi.get).toHaveBeenCalledWith('/drones', { params: undefined })
      expect(result).toEqual([mockDrone])
    })

    it('should fetch drones with custom parameters', async () => {
      const params = { skip: 10, limit: 5, status: 'online' }
      const mockResponse = { data: [mockDrone] }
      mockedApi.get.mockResolvedValue(mockResponse)

      const result = await droneService.getDrones(params)

      expect(mockedApi.get).toHaveBeenCalledWith('/drones', { params })
      expect(result).toEqual([mockDrone])
    })
  })

  describe('getDrone', () => {
    it('should fetch a specific drone by ID', async () => {
      const droneId = 'test-drone-1'
      const mockResponse = { data: mockDrone }
      mockedApi.get.mockResolvedValue(mockResponse)

      const result = await droneService.getDrone(droneId)

      expect(mockedApi.get).toHaveBeenCalledWith(`/drones/${droneId}`)
      expect(result).toEqual(mockDrone)
    })
  })

  describe('createDrone', () => {
    it('should create a new drone', async () => {
      const droneData = {
        drone_id: 'new-drone',
        name: 'New Drone',
        battery_level: 100,
        position_lat: 40.7128,
        position_lng: -74.0060,
        position_alt: 30
      }
      const mockResponse = { data: { ...mockDrone, ...droneData } }
      mockedApi.post.mockResolvedValue(mockResponse)

      const result = await droneService.createDrone(droneData)

      expect(mockedApi.post).toHaveBeenCalledWith('/drones', droneData)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('updateDrone', () => {
    it('should update an existing drone', async () => {
      const droneId = 'test-drone-1'
      const updateData = { battery_level: 75, name: 'Updated Name' }
      const mockResponse = { data: { ...mockDrone, ...updateData } }
      mockedApi.put.mockResolvedValue(mockResponse)

      const result = await droneService.updateDrone(droneId, updateData)

      expect(mockedApi.put).toHaveBeenCalledWith(`/drones/${droneId}`, updateData)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('deleteDrone', () => {
    it('should delete a drone', async () => {
      const droneId = 'test-drone-1'
      const mockResponse = { data: { message: 'Drone deleted successfully' } }
      mockedApi.delete.mockResolvedValue(mockResponse)

      const result = await droneService.deleteDrone(droneId)

      expect(mockedApi.delete).toHaveBeenCalledWith(`/drones/${droneId}`)
      expect(result).toEqual(mockResponse.data)
    })
  })

  describe('updateDronePosition', () => {
    it('should update drone position', async () => {
      const droneId = 'test-drone-1'
      const position = { lat: 40.7128, lng: -74.0060, alt: 30 }
      const mockResponse = { data: mockDrone }
      mockedApi.put.mockResolvedValue(mockResponse)

      const result = await droneService.updateDronePosition(droneId, position)

      expect(mockedApi.put).toHaveBeenCalledWith(`/drones/${droneId}/position`, position)
      expect(result).toEqual(mockDrone)
    })
  })

  describe('getDroneTelemetry', () => {
    it('should fetch drone telemetry data', async () => {
      const droneId = 'test-drone-1'
      const params = { start: '2024-01-01', end: '2024-01-02' }
      const mockTelemetry = [
        { timestamp: '2024-01-01T00:00:00Z', battery_level: 85 },
        { timestamp: '2024-01-01T01:00:00Z', battery_level: 80 }
      ]
      const mockResponse = { data: mockTelemetry }
      mockedApi.get.mockResolvedValue(mockResponse)

      const result = await droneService.getDroneTelemetry(droneId, params)

      expect(mockedApi.get).toHaveBeenCalledWith(`/drones/${droneId}/telemetry`, { params })
      expect(result).toEqual(mockTelemetry)
    })
  })
})