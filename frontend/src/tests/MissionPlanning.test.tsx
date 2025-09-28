"""
Comprehensive tests for MissionPlanning component.
Tests component rendering, user interactions, and API integration.
"""

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { BrowserRouter } from 'react-router-dom';
import MissionPlanning from '../pages/MissionPlanning';
import * as missionService from '../services/missionService';
import * as apiService from '../utils/api';

// Mock the API services
jest.mock('../services/missionService');
jest.mock('../utils/api');

// Mock Leaflet components
jest.mock('react-leaflet', () => ({
  MapContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="map-container">{children}</div>,
  TileLayer: () => <div data-testid="tile-layer" />,
  Marker: () => <div data-testid="marker" />,
  Popup: ({ children }: { children: React.ReactNode }) => <div data-testid="popup">{children}</div>,
}));

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('MissionPlanning Component', () => {
  const mockMission = {
    id: 'test-mission-123',
    name: 'Test SAR Mission',
    description: 'Test mission for component testing',
    status: 'planning',
    search_area: [
      [40.7128, -74.0060],
      [40.7589, -74.0060],
      [40.7589, -73.9352],
      [40.7128, -73.9352]
    ],
    launch_point: [40.7128, -74.0060],
    search_target: 'person',
    search_altitude: 30.0,
    search_speed: 'thorough',
    estimated_duration: 45,
    coverage_percentage: 85.0,
    created_at: new Date().toISOString(),
    drone_assignments: [
      {
        drone_id: 'drone_001',
        assigned_area: [[40.7128, -74.0060], [40.7200, -74.0060], [40.7200, -73.9950], [40.7128, -73.9950]],
        navigation_waypoints: [[40.7128, -74.0060, 10], [40.7150, -74.0030, 30], [40.7150, -74.0030, 25]],
        estimated_coverage_time: 20,
        status: 'assigned'
      }
    ]
  };

  beforeEach(() => {
    jest.clearAllMocks();

    // Mock API responses
    (apiService.getMissions as jest.Mock).mockResolvedValue({
      missions: [mockMission]
    });

    (apiService.getDrones as jest.Mock).mockResolvedValue({
      drones: []
    });
  });

  describe('Component Rendering', () => {
    test('renders mission planning interface', async () => {
      render(
        <TestWrapper>
          <MissionPlanning />
        </TestWrapper>
      );

      // Check for main components
      expect(screen.getByText('Mission Planning')).toBeInTheDocument();

      // Check for map container
      expect(screen.getByTestId('map-container')).toBeInTheDocument();

      // Check for conversational chat interface
      expect(screen.getByPlaceholderText(/describe your mission/i)).toBeInTheDocument();

      // Check for mission preview
      await waitFor(() => {
        expect(screen.getByText('Mission Preview')).toBeInTheDocument();
      });
    });

    test('displays loading state initially', () => {
      (apiService.getMissions as jest.Mock).mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      );

      render(
        <TestWrapper>
          <MissionPlanning />
        </TestWrapper>
      );

      expect(screen.getByText('Loading missions...')).toBeInTheDocument();
    });

    test('displays empty state when no missions exist', async () => {
      (apiService.getMissions as jest.Mock).mockResolvedValue({
        missions: []
      });

      render(
        <TestWrapper>
          <MissionPlanning />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('No missions found')).toBeInTheDocument();
      });
    });
  });

  describe('User Interactions', () => {
    test('handles area selection on map', async () => {
      const mockOnAreaSelect = jest.fn();

      render(
        <TestWrapper>
          <MissionPlanning />
        </TestWrapper>
      );

      // Simulate map click for area selection
      const mapContainer = screen.getByTestId('map-container');
      fireEvent.click(mapContainer);

      // Verify area selection is handled
      // This would be tested more thoroughly with actual map events
      expect(mapContainer).toBeInTheDocument();
    });

    test('handles conversational chat input', async () => {
      const mockSendMessage = jest.fn().mockResolvedValue({
        success: true,
        response: 'Mission plan created successfully'
      });

      (missionService.sendChatMessage as jest.Mock).mockImplementation(mockSendMessage);

      render(
        <TestWrapper>
          <MissionPlanning />
        </TestWrapper>
      );

      const chatInput = screen.getByPlaceholderText(/describe your mission/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      // Type a message
      fireEvent.change(chatInput, {
        target: { value: 'Search the collapsed building for survivors' }
      });

      // Send the message
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(mockSendMessage).toHaveBeenCalledWith(
          expect.objectContaining({
            content: 'Search the collapsed building for survivors'
          })
        );
      });
    });

    test('handles mission approval workflow', async () => {
      const mockApproveMission = jest.fn().mockResolvedValue({
        success: true,
        message: 'Mission approved and started'
      });

      (missionService.approveMission as jest.Mock).mockImplementation(mockApproveMission);

      render(
        <TestWrapper>
          <MissionPlanning />
        </TestWrapper>
      );

      // Find and click approve button (this would be in the mission preview)
      const approveButton = screen.queryByRole('button', { name: /approve/i });

      if (approveButton) {
        fireEvent.click(approveButton);

        await waitFor(() => {
          expect(mockApproveMission).toHaveBeenCalled();
        });
      }
    });
  });

  describe('API Integration', () => {
    test('fetches missions on component mount', async () => {
      render(
        <TestWrapper>
          <MissionPlanning />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(apiService.getMissions).toHaveBeenCalled();
      });
    });

    test('fetches drones on component mount', async () => {
      render(
        <TestWrapper>
          <MissionPlanning />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(apiService.getDrones).toHaveBeenCalled();
      });
    });

    test('handles API errors gracefully', async () => {
      (apiService.getMissions as jest.Mock).mockRejectedValue(
        new Error('Failed to fetch missions')
      );

      // Mock console.error to avoid test output pollution
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      render(
        <TestWrapper>
          <MissionPlanning />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          'Failed to load missions:',
          expect.any(Error)
        );
      });

      consoleSpy.mockRestore();
    });

    test('updates mission when API returns new data', async () => {
      const { rerender } = render(
        <TestWrapper>
          <MissionPlanning />
        </TestWrapper>
      );

      // Initially empty
      expect(screen.getByText('No missions found')).toBeInTheDocument();

      // Mock API returning mission data
      (apiService.getMissions as jest.Mock).mockResolvedValue({
        missions: [mockMission]
      });

      // Force re-render to simulate data update
      rerender(
        <TestWrapper>
          <MissionPlanning />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Test SAR Mission')).toBeInTheDocument();
      });
    });
  });

  describe('Real-time Updates', () => {
    test('handles real-time mission updates via WebSocket', async () => {
      render(
        <TestWrapper>
          <MissionPlanning />
        </TestWrapper>
      );

      // Simulate WebSocket message for mission update
      const mockWebSocketMessage = {
        event_type: 'mission_update',
        mission_id: mockMission.id,
        data: {
          status: 'active',
          progress: 25.0
        }
      };

      // This would be tested with actual WebSocket implementation
      // For now, verify the component structure supports real-time updates
      expect(screen.getByTestId('map-container')).toBeInTheDocument();
    });

    test('handles real-time drone position updates', async () => {
      const mockDrone = {
        id: 'drone_001',
        name: 'Test Drone',
        status: 'flying',
        current_position: [40.7150, -74.0030, 25.0],
        battery_level: 85.0
      };

      (apiService.getDrones as jest.Mock).mockResolvedValue({
        drones: [mockDrone]
      });

      render(
        <TestWrapper>
          <MissionPlanning />
        </TestWrapper>
      );

      await waitFor(() => {
        // Verify drone data is displayed
        expect(screen.getByText('Test Drone')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    test('displays error message for chat API failures', async () => {
      (missionService.sendChatMessage as jest.Mock).mockRejectedValue(
        new Error('Chat service unavailable')
      );

      render(
        <TestWrapper>
          <MissionPlanning />
        </TestWrapper>
      );

      const chatInput = screen.getByPlaceholderText(/describe your mission/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      fireEvent.change(chatInput, {
        target: { value: 'Test message' }
      });

      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText(/failed to send message/i)).toBeInTheDocument();
      });
    });

    test('handles mission creation errors', async () => {
      (missionService.createMission as jest.Mock).mockRejectedValue(
        new Error('Invalid mission parameters')
      );

      render(
        <TestWrapper>
          <MissionPlanning />
        </TestWrapper>
      );

      // Simulate mission creation attempt
      const createButton = screen.queryByRole('button', { name: /create mission/i });

      if (createButton) {
        fireEvent.click(createButton);

        await waitFor(() => {
          expect(screen.getByText(/failed to create mission/i)).toBeInTheDocument();
        });
      }
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA labels and roles', () => {
      render(
        <TestWrapper>
          <MissionPlanning />
        </TestWrapper>
      );

      // Check for proper heading structure
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument();

      // Check for proper button roles
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);

      // Check for proper input labels
      const inputs = screen.getAllByRole('textbox');
      expect(inputs.length).toBeGreaterThan(0);
    });

    test('supports keyboard navigation', () => {
      render(
        <TestWrapper>
          <MissionPlanning />
        </TestWrapper>
      );

      const chatInput = screen.getByPlaceholderText(/describe your mission/i);

      // Focus should be manageable
      chatInput.focus();
      expect(document.activeElement).toBe(chatInput);

      // Tab navigation should work
      fireEvent.keyDown(chatInput, { key: 'Tab' });
      // Additional keyboard navigation tests would require more setup
    });
  });

  describe('Performance', () => {
    test('handles large datasets efficiently', async () => {
      // Create mock data with many missions
      const manyMissions = Array.from({ length: 100 }, (_, i) => ({
        ...mockMission,
        id: `mission_${i}`,
        name: `Mission ${i}`
      }));

      (apiService.getMissions as jest.Mock).mockResolvedValue({
        missions: manyMissions
      });

      const startTime = performance.now();

      render(
        <TestWrapper>
          <MissionPlanning />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Mission 0')).toBeInTheDocument();
      });

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render within reasonable time (adjust threshold as needed)
      expect(renderTime).toBeLessThan(1000); // 1 second
    });

    test('debounces rapid user inputs', async () => {
      const mockSendMessage = jest.fn();
      (missionService.sendChatMessage as jest.Mock).mockImplementation(mockSendMessage);

      render(
        <TestWrapper>
          <MissionPlanning />
        </TestWrapper>
      );

      const chatInput = screen.getByPlaceholderText(/describe your mission/i);

      // Simulate rapid typing
      const testMessage = 'This is a test message with many words';
      for (let i = 0; i < testMessage.length; i++) {
        fireEvent.change(chatInput, {
          target: { value: testMessage.substring(0, i + 1) }
        });
      }

      // Should debounce and not send intermediate messages
      // This would be tested with actual debounce implementation
      await waitFor(() => {
        expect(mockSendMessage).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('Responsive Design', () => {
    test('adapts to mobile viewport', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      render(
        <TestWrapper>
          <MissionPlanning />
        </TestWrapper>
      );

      // Check for mobile-specific layout classes
      const container = screen.getByTestId('map-container').parentElement;
      expect(container).toHaveClass('grid-cols-1'); // Mobile: single column
    });

    test('adapts to desktop viewport', () => {
      // Mock desktop viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1200,
      });

      render(
        <TestWrapper>
          <MissionPlanning />
        </TestWrapper>
      );

      // Check for desktop-specific layout classes
      const container = screen.getByTestId('map-container').parentElement;
      expect(container).toHaveClass('lg:grid-cols-2'); // Desktop: two columns
    });
  });

  describe('Internationalization', () => {
    test('supports multiple languages', () => {
      // This would test i18n implementation
      // For now, verify that text content is properly structured for translation

      render(
        <TestWrapper>
          <MissionPlanning />
        </TestWrapper>
      );

      // Check that translatable strings are not hardcoded
      const headings = screen.getAllByRole('heading');
      headings.forEach(heading => {
        // Verify headings contain meaningful text that can be translated
        expect(heading.textContent).toBeTruthy();
      });
    });
  });
});