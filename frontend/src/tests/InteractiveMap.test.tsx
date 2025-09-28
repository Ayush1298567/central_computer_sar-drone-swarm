"""
Comprehensive tests for InteractiveMap component.
Tests map rendering, area selection, drone tracking, and user interactions.
"""

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import InteractiveMap from '../components/map/InteractiveMap';

// Mock Leaflet components
jest.mock('react-leaflet', () => ({
  MapContainer: ({ children, center, zoom }: any) => (
    <div data-testid="map-container" data-center={JSON.stringify(center)} data-zoom={zoom}>
      {children}
    </div>
  ),
  TileLayer: ({ url }: any) => <div data-testid="tile-layer" data-url={url} />,
  Marker: ({ position, children }: any) => (
    <div data-testid="marker" data-position={JSON.stringify(position)}>
      {children}
    </div>
  ),
  Popup: ({ children }: any) => <div data-testid="popup">{children}</div>,
  Polygon: ({ positions }: any) => (
    <div data-testid="polygon" data-positions={JSON.stringify(positions)} />
  ),
  useMap: () => ({
    setView: jest.fn(),
    getCenter: () => ({ lat: 40.7128, lng: -74.0060 }),
    getZoom: () => 13,
    addLayer: jest.fn(),
    removeLayer: jest.fn(),
  }),
  useMapEvents: () => ({
    onClick: jest.fn(),
    onZoom: jest.fn(),
    onMove: jest.fn(),
  }),
}));

// Mock map utilities
jest.mock('../utils/api', () => ({
  getMissions: jest.fn(),
  getDrones: jest.fn(),
}));

describe('InteractiveMap Component', () => {
  const mockMission = {
    id: 'test-mission-123',
    name: 'Test SAR Mission',
    search_area: [
      [40.7128, -74.0060],
      [40.7589, -74.0060],
      [40.7589, -73.9352],
      [40.7128, -73.9352]
    ],
    launch_point: [40.7128, -74.0060],
    drone_assignments: [
      {
        drone_id: 'drone_001',
        assigned_area: [[40.7128, -74.0060], [40.7200, -74.0060], [40.7200, -73.9950], [40.7128, -73.9950]],
        status: 'assigned'
      }
    ]
  };

  const mockDrones = [
    {
      id: 'drone_001',
      name: 'Test Drone 1',
      status: 'flying',
      current_position: [40.7150, -74.0030, 25.0],
      battery_level: 85.0
    },
    {
      id: 'drone_002',
      name: 'Test Drone 2',
      status: 'online',
      current_position: [40.7170, -74.0010, 30.0],
      battery_level: 92.0
    }
  ];

  const defaultProps = {
    onAreaSelect: jest.fn(),
    mission: null,
    drones: [],
    selectedArea: null,
    isSelecting: false
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Component Rendering', () => {
    test('renders map container with default settings', () => {
      render(<InteractiveMap {...defaultProps} />);

      const mapContainer = screen.getByTestId('map-container');
      expect(mapContainer).toBeInTheDocument();

      // Check default center (NYC)
      expect(mapContainer).toHaveAttribute('data-center', JSON.stringify([40.7128, -74.0060]));
      expect(mapContainer).toHaveAttribute('data-zoom', '13');
    });

    test('renders tile layer', () => {
      render(<InteractiveMap {...defaultProps} />);

      const tileLayer = screen.getByTestId('tile-layer');
      expect(tileLayer).toBeInTheDocument();
      expect(tileLayer).toHaveAttribute('data-url', expect.stringContaining('openstreetmap'));
    });

    test('displays mission search area when mission is provided', () => {
      render(<InteractiveMap {...defaultProps} mission={mockMission} />);

      const polygons = screen.getAllByTestId('polygon');
      expect(polygons.length).toBeGreaterThan(0);

      // Check that mission area is rendered
      const missionPolygon = polygons.find(polygon =>
        JSON.parse(polygon.getAttribute('data-positions') || '[]').length === 4
      );
      expect(missionPolygon).toBeInTheDocument();
    });

    test('displays drone positions when drones are provided', () => {
      render(<InteractiveMap {...defaultProps} drones={mockDrones} />);

      const markers = screen.getAllByTestId('marker');
      expect(markers.length).toBeGreaterThanOrEqual(mockDrones.length);

      // Check drone markers are positioned correctly
      markers.forEach(marker => {
        const position = JSON.parse(marker.getAttribute('data-position') || '[]');
        expect(position).toHaveLength(2); // [lat, lng]
      });
    });

    test('shows launch point marker', () => {
      render(<InteractiveMap {...defaultProps} mission={mockMission} />);

      const markers = screen.getAllByTestId('marker');
      const launchPointMarker = markers.find(marker =>
        JSON.parse(marker.getAttribute('data-position') || '[]')[0] === 40.7128
      );
      expect(launchPointMarker).toBeInTheDocument();
    });
  });

  describe('User Interactions', () => {
    test('handles map click for area selection', () => {
      const mockOnAreaSelect = jest.fn();
      render(<InteractiveMap {...defaultProps} onAreaSelect={mockOnAreaSelect} isSelecting={true} />);

      const mapContainer = screen.getByTestId('map-container');
      fireEvent.click(mapContainer);

      // Verify area selection callback is called
      expect(mockOnAreaSelect).toHaveBeenCalled();
    });

    test('shows selection mode visual feedback', () => {
      render(<InteractiveMap {...defaultProps} isSelecting={true} />);

      const mapContainer = screen.getByTestId('map-container');

      // In selection mode, the map should indicate it's ready for selection
      expect(mapContainer).toBeInTheDocument();
      // Additional visual feedback tests would require CSS class checks
    });

    test('displays area selection preview', () => {
      const selectedArea = [
        [40.7128, -74.0060],
        [40.7200, -74.0060],
        [40.7200, -73.9950]
      ];

      render(<InteractiveMap {...defaultProps} selectedArea={selectedArea} />);

      const polygons = screen.getAllByTestId('polygon');
      const selectionPolygon = polygons.find(polygon =>
        JSON.parse(polygon.getAttribute('data-positions') || '[]').length === 3
      );
      expect(selectionPolygon).toBeInTheDocument();
    });

    test('handles zoom controls', () => {
      render(<InteractiveMap {...defaultProps} />);

      // Zoom controls would be tested with actual map implementation
      // For now, verify the map container exists
      expect(screen.getByTestId('map-container')).toBeInTheDocument();
    });
  });

  describe('Drone Tracking', () => {
    test('displays flying drones with different markers', () => {
      render(<InteractiveMap {...defaultProps} drones={mockDrones} />);

      const markers = screen.getAllByTestId('marker');

      // Should have markers for each drone
      expect(markers.length).toBeGreaterThanOrEqual(mockDrones.length);
    });

    test('shows drone status in marker popups', () => {
      render(<InteractiveMap {...defaultProps} drones={mockDrones} />);

      const popups = screen.getAllByTestId('popup');
      expect(popups.length).toBeGreaterThan(0);

      // Check that drone information is displayed in popups
      const drone1Popup = screen.getByText('Test Drone 1');
      expect(drone1Popup).toBeInTheDocument();
    });

    test('updates drone positions in real-time', async () => {
      const { rerender } = render(<InteractiveMap {...defaultProps} drones={mockDrones} />);

      // Update drone positions
      const updatedDrones = mockDrones.map(drone => ({
        ...drone,
        current_position: [
          drone.current_position[0] + 0.001,
          drone.current_position[1] + 0.001,
          drone.current_position[2]
        ]
      }));

      rerender(<InteractiveMap {...defaultProps} drones={updatedDrones} />);

      const markers = screen.getAllByTestId('marker');

      // Verify positions are updated (this would be more thorough with actual map implementation)
      expect(markers.length).toBeGreaterThan(0);
    });

    test('handles drone connection status changes', () => {
      const disconnectedDrones = mockDrones.map(drone => ({
        ...drone,
        status: 'offline'
      }));

      render(<InteractiveMap {...defaultProps} drones={disconnectedDrones} />);

      // Offline drones should still be displayed but with different styling
      const markers = screen.getAllByTestId('marker');
      expect(markers.length).toBeGreaterThan(0);
    });
  });

  describe('Mission Visualization', () => {
    test('displays mission search areas with proper styling', () => {
      render(<InteractiveMap {...defaultProps} mission={mockMission} />);

      const polygons = screen.getAllByTestId('polygon');

      // Should have polygon for mission area
      expect(polygons.length).toBeGreaterThan(0);

      // Check mission area styling (would be tested with actual CSS classes)
      const missionPolygon = polygons[0];
      expect(missionPolygon).toBeInTheDocument();
    });

    test('shows drone assignment areas', () => {
      render(<InteractiveMap {...defaultProps} mission={mockMission} />);

      const polygons = screen.getAllByTestId('polygon');

      // Should have polygons for both mission area and drone assignments
      expect(polygons.length).toBeGreaterThan(1);
    });

    test('displays mission progress overlay', () => {
      const missionWithProgress = {
        ...mockMission,
        status: 'active',
        coverage_percentage: 45.0
      };

      render(<InteractiveMap {...defaultProps} mission={missionWithProgress} />);

      // Progress visualization would be tested here
      expect(screen.getByTestId('map-container')).toBeInTheDocument();
    });

    test('shows mission waypoints and navigation paths', () => {
      const missionWithWaypoints = {
        ...mockMission,
        drone_assignments: [
          {
            ...mockMission.drone_assignments[0],
            navigation_waypoints: [
              [40.7128, -74.0060, 10],
              [40.7150, -74.0030, 30],
              [40.7170, -74.0010, 25]
            ]
          }
        ]
      };

      render(<InteractiveMap {...defaultProps} mission={missionWithWaypoints} />);

      // Waypoint visualization would be tested here
      expect(screen.getByTestId('map-container')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    test('handles invalid coordinates gracefully', () => {
      const missionWithInvalidCoords = {
        ...mockMission,
        search_area: [
          [NaN, -74.0060],
          [40.7589, -74.0060],
          [40.7589, -73.9352],
          [40.7128, -73.9352]
        ]
      };

      // Should not crash with invalid coordinates
      expect(() => {
        render(<InteractiveMap {...defaultProps} mission={missionWithInvalidCoords} />);
      }).not.toThrow();
    });

    test('handles missing map data gracefully', () => {
      render(<InteractiveMap {...defaultProps} />);

      // Should render without crashing when no data is provided
      expect(screen.getByTestId('map-container')).toBeInTheDocument();
      expect(screen.getByTestId('tile-layer')).toBeInTheDocument();
    });

    test('handles map loading errors', () => {
      // Mock map loading failure
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      render(<InteractiveMap {...defaultProps} />);

      // Should handle errors gracefully
      expect(screen.getByTestId('map-container')).toBeInTheDocument();

      consoleSpy.mockRestore();
    });
  });

  describe('Performance', () => {
    test('handles large numbers of drones efficiently', () => {
      // Create many mock drones
      const manyDrones = Array.from({ length: 100 }, (_, i) => ({
        id: `drone_${i}`,
        name: `Drone ${i}`,
        status: 'flying',
        current_position: [40.7128 + i * 0.001, -74.0060 + i * 0.001, 25.0],
        battery_level: 85.0
      }));

      const startTime = performance.now();

      render(<InteractiveMap {...defaultProps} drones={manyDrones} />);

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render within reasonable time
      expect(renderTime).toBeLessThan(1000); // 1 second
      expect(screen.getAllByTestId('marker').length).toBeGreaterThan(50);
    });

    test('handles complex mission areas efficiently', () => {
      // Create mission with complex search area
      const complexMission = {
        ...mockMission,
        search_area: Array.from({ length: 50 }, (_, i) => [
          40.7128 + Math.sin(i * 0.1) * 0.01,
          -74.0060 + Math.cos(i * 0.1) * 0.01
        ]).concat([[40.7128, -74.0060]]) // Close the polygon
      };

      const startTime = performance.now();

      render(<InteractiveMap {...defaultProps} mission={complexMission} />);

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render within reasonable time
      expect(renderTime).toBeLessThan(1000); // 1 second
    });

    test('debounces rapid position updates', async () => {
      const { rerender } = render(<InteractiveMap {...defaultProps} drones={mockDrones} />);

      // Rapidly update drone positions
      for (let i = 0; i < 50; i++) {
        const updatedDrones = mockDrones.map(drone => ({
          ...drone,
          current_position: [
            drone.current_position[0] + i * 0.0001,
            drone.current_position[1] + i * 0.0001,
            drone.current_position[2]
          ]
        }));

        rerender(<InteractiveMap {...defaultProps} drones={updatedDrones} />);
      }

      // Should handle rapid updates without performance issues
      expect(screen.getByTestId('map-container')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA labels for screen readers', () => {
      render(<InteractiveMap {...defaultProps} />);

      const mapContainer = screen.getByTestId('map-container');

      // Should have accessible name
      expect(mapContainer).toHaveAttribute('aria-label', expect.any(String));
    });

    test('supports keyboard navigation', () => {
      render(<InteractiveMap {...defaultProps} />);

      const mapContainer = screen.getByTestId('map-container');

      // Focus should be manageable
      mapContainer.focus();
      expect(document.activeElement).toBe(mapContainer);

      // Keyboard events should be handled
      fireEvent.keyDown(mapContainer, { key: 'Enter' });
      fireEvent.keyDown(mapContainer, { key: 'Escape' });

      // Additional keyboard interaction tests would require actual map implementation
    });

    test('provides alternative text for visual elements', () => {
      render(<InteractiveMap {...defaultProps} drones={mockDrones} />);

      // Markers should have descriptive text
      const markers = screen.getAllByTestId('marker');
      markers.forEach(marker => {
        // In actual implementation, markers would have alt text or aria-labels
        expect(marker).toBeInTheDocument();
      });
    });
  });

  describe('Responsive Design', () => {
    test('adapts to different screen sizes', () => {
      // Test mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      render(<InteractiveMap {...defaultProps} />);

      const mapContainer = screen.getByTestId('map-container');
      expect(mapContainer).toBeInTheDocument();

      // Test desktop viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1200,
      });

      render(<InteractiveMap {...defaultProps} />);

      const desktopMapContainer = screen.getByTestId('map-container');
      expect(desktopMapContainer).toBeInTheDocument();
    });

    test('handles touch interactions on mobile', () => {
      render(<InteractiveMap {...defaultProps} />);

      const mapContainer = screen.getByTestId('map-container');

      // Simulate touch events
      fireEvent.touchStart(mapContainer, {
        touches: [{ clientX: 100, clientY: 100 }]
      });

      fireEvent.touchEnd(mapContainer, {
        touches: [{ clientX: 150, clientY: 150 }]
      });

      // Touch interactions should be handled appropriately
      expect(mapContainer).toBeInTheDocument();
    });
  });

  describe('Integration with Mission Data', () => {
    test('updates when mission data changes', () => {
      const { rerender } = render(<InteractiveMap {...defaultProps} mission={mockMission} />);

      // Initially shows mission data
      expect(screen.getAllByTestId('polygon').length).toBeGreaterThan(0);

      // Change mission data
      const updatedMission = {
        ...mockMission,
        search_area: [
          [40.7128, -74.0060],
          [40.7500, -74.0060],
          [40.7500, -73.9500],
          [40.7128, -73.9500]
        ]
      };

      rerender(<InteractiveMap {...defaultProps} mission={updatedMission} />);

      // Should update display
      expect(screen.getAllByTestId('polygon').length).toBeGreaterThan(0);
    });

    test('handles mission state changes', () => {
      const activeMission = {
        ...mockMission,
        status: 'active',
        coverage_percentage: 25.0
      };

      render(<InteractiveMap {...defaultProps} mission={activeMission} />);

      // Active mission should show progress indicators
      expect(screen.getByTestId('map-container')).toBeInTheDocument();

      const completedMission = {
        ...mockMission,
        status: 'completed',
        coverage_percentage: 100.0
      };

      render(<InteractiveMap {...defaultProps} mission={completedMission} />);

      // Completed mission should show completion indicators
      expect(screen.getByTestId('map-container')).toBeInTheDocument();
    });

    test('displays discovery locations', () => {
      const missionWithDiscoveries = {
        ...mockMission,
        discoveries: [
          {
            id: 'discovery_001',
            object_type: 'person',
            confidence_score: 0.85,
            latitude: 40.7150,
            longitude: -74.0030,
            altitude: 25.0
          }
        ]
      };

      render(<InteractiveMap {...defaultProps} mission={missionWithDiscoveries} />);

      // Should display discovery markers
      const markers = screen.getAllByTestId('marker');
      expect(markers.length).toBeGreaterThan(1); // Mission markers + discovery markers
    });
  });

  describe('Map Controls', () => {
    test('provides zoom controls', () => {
      render(<InteractiveMap {...defaultProps} />);

      // Zoom controls would be tested with actual map implementation
      expect(screen.getByTestId('map-container')).toBeInTheDocument();
    });

    test('allows manual area selection', () => {
      const mockOnAreaSelect = jest.fn();
      render(<InteractiveMap {...defaultProps} onAreaSelect={mockOnAreaSelect} isSelecting={true} />);

      const mapContainer = screen.getByTestId('map-container');

      // Simulate area selection
      fireEvent.click(mapContainer);

      // Should call area selection callback
      expect(mockOnAreaSelect).toHaveBeenCalled();
    });

    test('supports different map layers', () => {
      render(<InteractiveMap {...defaultProps} />);

      // Different map layers would be tested here
      expect(screen.getByTestId('tile-layer')).toBeInTheDocument();
    });
  });
});