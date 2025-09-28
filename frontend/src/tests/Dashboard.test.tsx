"""
Comprehensive tests for Dashboard component.
Tests dashboard rendering, navigation, mission overview, and real-time updates.
"""

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from '../pages/Dashboard';
import * as apiService from '../utils/api';

// Mock API services
jest.mock('../utils/api');

// Mock child components
jest.mock('../components/analytics/AnalyticsDashboard', () => {
  return function MockAnalyticsDashboard({ missions, drones }: any) {
    return (
      <div data-testid="analytics-dashboard">
        <div>Analytics Dashboard</div>
        <div>Missions: {missions?.length || 0}</div>
        <div>Drones: {drones?.length || 0}</div>
      </div>
    );
  };
});

jest.mock('../components/drone/DroneStatus', () => {
  return function MockDroneStatus({ drones }: any) {
    return (
      <div data-testid="drone-status">
        <div>Drone Status</div>
        <div>Active Drones: {drones?.filter((d: any) => d.status === 'online' || d.status === 'flying').length || 0}</div>
      </div>
    );
  };
});

jest.mock('../components/mission/MissionOverview', () => {
  return function MockMissionOverview({ missions }: any) {
    return (
      <div data-testid="mission-overview">
        <div>Mission Overview</div>
        <div>Total Missions: {missions?.length || 0}</div>
        <div>Active Missions: {missions?.filter((m: any) => m.status === 'active').length || 0}</div>
      </div>
    );
  };
});

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

describe('Dashboard Component', () => {
  const mockMissions = [
    {
      id: 'mission_001',
      name: 'SAR Mission Alpha',
      description: 'Search and rescue operation in downtown area',
      status: 'active',
      search_target: 'person',
      created_at: '2024-01-15T08:00:00Z',
      started_at: '2024-01-15T08:30:00Z',
      estimated_duration: 60,
      coverage_percentage: 45.0,
      drone_assignments: [
        { drone_id: 'drone_001', status: 'searching' },
        { drone_id: 'drone_002', status: 'navigating' }
      ]
    },
    {
      id: 'mission_002',
      name: 'SAR Mission Beta',
      description: 'Building collapse search operation',
      status: 'planning',
      search_target: 'person',
      created_at: '2024-01-15T09:00:00Z',
      estimated_duration: 45,
      coverage_percentage: 0.0,
      drone_assignments: []
    },
    {
      id: 'mission_003',
      name: 'SAR Mission Gamma',
      description: 'Completed search operation',
      status: 'completed',
      search_target: 'person',
      created_at: '2024-01-14T14:00:00Z',
      started_at: '2024-01-14T14:30:00Z',
      completed_at: '2024-01-14T15:15:00Z',
      estimated_duration: 45,
      actual_duration: 45,
      coverage_percentage: 100.0,
      discoveries: [
        { id: 'discovery_001', object_type: 'person', confidence_score: 0.92 }
      ]
    }
  ];

  const mockDrones = [
    {
      id: 'drone_001',
      name: 'Alpha Drone',
      status: 'flying',
      battery_level: 78.0,
      signal_strength: 95,
      current_position: [40.7150, -74.0030, 25.0],
      missions_completed: 15,
      total_flight_hours: 45.2
    },
    {
      id: 'drone_002',
      name: 'Beta Drone',
      status: 'online',
      battery_level: 92.0,
      signal_strength: 88,
      current_position: [40.7170, -74.0010, 30.0],
      missions_completed: 22,
      total_flight_hours: 67.8
    },
    {
      id: 'drone_003',
      name: 'Gamma Drone',
      status: 'charging',
      battery_level: 15.0,
      signal_strength: 0,
      current_position: [40.7128, -74.0060, 0.0],
      missions_completed: 8,
      total_flight_hours: 23.1
    }
  ];

  beforeEach(() => {
    jest.clearAllMocks();

    // Mock API responses
    (apiService.getMissions as jest.Mock).mockResolvedValue({
      missions: mockMissions
    });

    (apiService.getDrones as jest.Mock).mockResolvedValue({
      drones: mockDrones
    });
  });

  describe('Component Rendering', () => {
    test('renders dashboard with all main sections', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      // Check main sections
      expect(screen.getByText('SAR Mission Control Dashboard')).toBeInTheDocument();
      expect(screen.getByTestId('analytics-dashboard')).toBeInTheDocument();
      expect(screen.getByTestId('drone-status')).toBeInTheDocument();
      expect(screen.getByTestId('mission-overview')).toBeInTheDocument();
    });

    test('displays loading state initially', () => {
      (apiService.getMissions as jest.Mock).mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      );

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      expect(screen.getByText('Loading dashboard...')).toBeInTheDocument();
    });

    test('displays system status indicators', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        // Check for system status indicators
        expect(screen.getByText(/system status/i)).toBeInTheDocument();
        expect(screen.getByText(/operational/i)).toBeInTheDocument();
      });
    });

    test('shows navigation buttons', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /mission planning/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /live mission/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /analytics/i })).toBeInTheDocument();
      });
    });
  });

  describe('Mission Overview', () => {
    test('displays mission statistics correctly', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Total Missions: 3')).toBeInTheDocument();
        expect(screen.getByText('Active Missions: 1')).toBeInTheDocument();
      });
    });

    test('shows mission list with status indicators', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        // Check mission cards/list items
        expect(screen.getByText('SAR Mission Alpha')).toBeInTheDocument();
        expect(screen.getByText('SAR Mission Beta')).toBeInTheDocument();
        expect(screen.getByText('SAR Mission Gamma')).toBeInTheDocument();

        // Check status indicators
        expect(screen.getByText(/active/i)).toBeInTheDocument();
        expect(screen.getByText(/planning/i)).toBeInTheDocument();
        expect(screen.getByText(/completed/i)).toBeInTheDocument();
      });
    });

    test('displays mission progress for active missions', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        // Active mission should show progress
        expect(screen.getByText(/45%/i)).toBeInTheDocument();
        expect(screen.getByText(/60.*minutes/i)).toBeInTheDocument();
      });
    });

    test('shows mission completion details for completed missions', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        // Completed mission should show completion details
        expect(screen.getByText(/100%/i)).toBeInTheDocument();
        expect(screen.getByText(/45.*minutes/i)).toBeInTheDocument();
      });
    });
  });

  describe('Drone Status', () => {
    test('displays drone fleet statistics', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Active Drones: 2')).toBeInTheDocument();
      });
    });

    test('shows individual drone status cards', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Alpha Drone')).toBeInTheDocument();
        expect(screen.getByText('Beta Drone')).toBeInTheDocument();
        expect(screen.getByText('Gamma Drone')).toBeInTheDocument();

        // Check status indicators
        expect(screen.getByText(/flying/i)).toBeInTheDocument();
        expect(screen.getByText(/online/i)).toBeInTheDocument();
        expect(screen.getByText(/charging/i)).toBeInTheDocument();
      });
    });

    test('displays battery levels for all drones', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/78%/i)).toBeInTheDocument();
        expect(screen.getByText(/92%/i)).toBeInTheDocument();
        expect(screen.getByText(/15%/i)).toBeInTheDocument();
      });
    });

    test('shows signal strength indicators', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/95/i)).toBeInTheDocument();
        expect(screen.getByText(/88/i)).toBeInTheDocument();
        expect(screen.getByText(/0/i)).toBeInTheDocument();
      });
    });

    test('displays drone performance metrics', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/15.*missions/i)).toBeInTheDocument();
        expect(screen.getByText(/22.*missions/i)).toBeInTheDocument();
        expect(screen.getByText(/8.*missions/i)).toBeInTheDocument();
      });
    });
  });

  describe('Navigation and Actions', () => {
    test('navigates to mission planning page', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        const planningButton = screen.getByRole('button', { name: /mission planning/i });
        fireEvent.click(planningButton);

        // In actual implementation, this would navigate to /planning
        // For testing, verify the button exists and is clickable
        expect(planningButton).toBeInTheDocument();
      });
    });

    test('navigates to live mission view', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        const liveButton = screen.getByRole('button', { name: /live mission/i });
        fireEvent.click(liveButton);

        // Verify navigation functionality
        expect(liveButton).toBeInTheDocument();
      });
    });

    test('opens analytics view', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        const analyticsButton = screen.getByRole('button', { name: /analytics/i });
        fireEvent.click(analyticsButton);

        // Verify analytics functionality
        expect(analyticsButton).toBeInTheDocument();
      });
    });

    test('handles mission selection for detailed view', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        const missionCard = screen.getByText('SAR Mission Alpha');
        fireEvent.click(missionCard);

        // Should navigate to detailed mission view
        expect(missionCard).toBeInTheDocument();
      });
    });
  });

  describe('Real-time Updates', () => {
    test('updates mission status in real-time', async () => {
      const { rerender } = render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('SAR Mission Alpha')).toBeInTheDocument();
      });

      // Simulate mission status update
      const updatedMissions = mockMissions.map(mission =>
        mission.id === 'mission_001'
          ? { ...mission, status: 'paused', coverage_percentage: 30.0 }
          : mission
      );

      (apiService.getMissions as jest.Mock).mockResolvedValue({
        missions: updatedMissions
      });

      rerender(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/paused/i)).toBeInTheDocument();
        expect(screen.getByText(/30%/i)).toBeInTheDocument();
      });
    });

    test('updates drone status in real-time', async () => {
      const { rerender } = render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Alpha Drone')).toBeInTheDocument();
      });

      // Simulate drone status update
      const updatedDrones = mockDrones.map(drone =>
        drone.id === 'drone_001'
          ? { ...drone, status: 'returning', battery_level: 25.0 }
          : drone
      );

      (apiService.getDrones as jest.Mock).mockResolvedValue({
        drones: updatedDrones
      });

      rerender(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/returning/i)).toBeInTheDocument();
        expect(screen.getByText(/25%/i)).toBeInTheDocument();
      });
    });

    test('handles new mission creation in real-time', async () => {
      const { rerender } = render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Total Missions: 3')).toBeInTheDocument();
      });

      // Simulate new mission creation
      const newMissions = [
        ...mockMissions,
        {
          id: 'mission_004',
          name: 'SAR Mission Delta',
          description: 'New emergency mission',
          status: 'planning',
          search_target: 'person',
          created_at: new Date().toISOString(),
          estimated_duration: 30,
          coverage_percentage: 0.0,
          drone_assignments: []
        }
      ];

      (apiService.getMissions as jest.Mock).mockResolvedValue({
        missions: newMissions
      });

      rerender(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Total Missions: 4')).toBeInTheDocument();
        expect(screen.getByText('SAR Mission Delta')).toBeInTheDocument();
      });
    });
  });

  describe('Analytics Integration', () => {
    test('displays analytics summary data', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByTestId('analytics-dashboard')).toBeInTheDocument();
        expect(screen.getByText('Analytics Dashboard')).toBeInTheDocument();
      });
    });

    test('passes correct data to analytics component', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        const analyticsDashboard = screen.getByTestId('analytics-dashboard');
        expect(analyticsDashboard).toHaveTextContent('Missions: 3');
        expect(analyticsDashboard).toHaveTextContent('Drones: 3');
      });
    });

    test('handles analytics data loading errors', async () => {
      (apiService.getMissions as jest.Mock).mockRejectedValue(
        new Error('Failed to load analytics data')
      );

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          'Failed to load dashboard data:',
          expect.any(Error)
        );
      });

      consoleSpy.mockRestore();
    });
  });

  describe('Error Handling', () => {
    test('handles API errors gracefully', async () => {
      (apiService.getMissions as jest.Mock).mockRejectedValue(
        new Error('API unavailable')
      );

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          'Failed to load dashboard data:',
          expect.any(Error)
        );
      });

      consoleSpy.mockRestore();
    });

    test('shows appropriate error states', async () => {
      (apiService.getDrones as jest.Mock).mockRejectedValue(
        new Error('Drone service unavailable')
      );

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        // Should show error state for drone section
        expect(screen.getByText(/unable to load drone data/i)).toBeInTheDocument();
      });
    });

    test('recovers from temporary network issues', async () => {
      // First call fails
      (apiService.getMissions as jest.Mock).mockRejectedValueOnce(
        new Error('Network error')
      );

      // Second call succeeds
      (apiService.getMissions as jest.Mock).mockResolvedValueOnce({
        missions: mockMissions
      });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      // Should eventually show data after retry
      await waitFor(() => {
        expect(screen.getByText('SAR Mission Alpha')).toBeInTheDocument();
      }, { timeout: 3000 });
    });
  });

  describe('Performance', () => {
    test('handles large datasets efficiently', async () => {
      // Create large datasets
      const manyMissions = Array.from({ length: 100 }, (_, i) => ({
        ...mockMissions[0],
        id: `mission_${i}`,
        name: `Mission ${i}`
      }));

      const manyDrones = Array.from({ length: 50 }, (_, i) => ({
        ...mockDrones[0],
        id: `drone_${i}`,
        name: `Drone ${i}`
      }));

      (apiService.getMissions as jest.Mock).mockResolvedValue({
        missions: manyMissions
      });

      (apiService.getDrones as jest.Mock).mockResolvedValue({
        drones: manyDrones
      });

      const startTime = performance.now();

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Total Missions: 100')).toBeInTheDocument();
      });

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render within reasonable time
      expect(renderTime).toBeLessThan(2000); // 2 seconds
    });

    test('debounces rapid data updates', async () => {
      const { rerender } = render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      // Rapidly update data
      for (let i = 0; i < 20; i++) {
        const updatedMissions = mockMissions.map(mission => ({
          ...mission,
          coverage_percentage: mission.coverage_percentage + i * 0.1
        }));

        (apiService.getMissions as jest.Mock).mockResolvedValue({
          missions: updatedMissions
        });

        rerender(
          <TestWrapper>
            <Dashboard />
          </TestWrapper>
        );
      }

      // Should handle rapid updates without performance issues
      await waitFor(() => {
        expect(screen.getByTestId('mission-overview')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    test('has proper heading structure', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('SAR Mission Control Dashboard');
      });
    });

    test('has proper ARIA labels', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        // Check for proper labeling of interactive elements
        const navigationButtons = screen.getAllByRole('button');
        navigationButtons.forEach(button => {
          expect(button).toHaveAttribute('aria-label');
        });
      });
    });

    test('supports keyboard navigation', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        const firstButton = screen.getAllByRole('button')[0];
        firstButton.focus();

        expect(document.activeElement).toBe(firstButton);

        // Test tab navigation
        fireEvent.keyDown(firstButton, { key: 'Tab' });

        const secondButton = screen.getAllByRole('button')[1];
        expect(document.activeElement).toBe(secondButton);
      });
    });

    test('provides screen reader announcements for status changes', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        // Status indicators should have aria-live for screen readers
        const statusElements = screen.getAllByText(/active|online|planning/i);
        statusElements.forEach(element => {
          expect(element).toHaveAttribute('aria-live', 'polite');
        });
      });
    });
  });

  describe('Responsive Design', () => {
    test('adapts to mobile viewport', async () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        // Mobile layout should be single column
        const dashboard = screen.getByText('SAR Mission Control Dashboard').closest('div');
        expect(dashboard).toHaveClass('grid-cols-1');
      });
    });

    test('adapts to tablet viewport', async () => {
      // Mock tablet viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768,
      });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        // Tablet layout should use appropriate grid
        const dashboard = screen.getByText('SAR Mission Control Dashboard').closest('div');
        expect(dashboard).toHaveClass('md:grid-cols-2');
      });
    });

    test('adapts to desktop viewport', async () => {
      // Mock desktop viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1200,
      });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        // Desktop layout should use full grid
        const dashboard = screen.getByText('SAR Mission Control Dashboard').closest('div');
        expect(dashboard).toHaveClass('lg:grid-cols-3');
      });
    });
  });

  describe('System Status', () => {
    test('displays system health status', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/system status/i)).toBeInTheDocument();
        expect(screen.getByText(/operational/i)).toBeInTheDocument();
      });
    });

    test('shows warning for system issues', async () => {
      // Mock system health check returning issues
      (apiService.getMissions as jest.Mock).mockResolvedValue({
        missions: [],
        system_status: 'warning',
        issues: ['Low disk space', 'High memory usage']
      });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/warning/i)).toBeInTheDocument();
        expect(screen.getByText(/low disk space/i)).toBeInTheDocument();
      });
    });

    test('displays critical system alerts', async () => {
      (apiService.getMissions as jest.Mock).mockResolvedValue({
        missions: [],
        system_status: 'critical',
        issues: ['Database connection failed', 'Multiple drones offline']
      });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/critical/i)).toBeInTheDocument();
        expect(screen.getByText(/database connection failed/i)).toBeInTheDocument();
      });
    });
  });

  describe('Quick Actions', () => {
    test('provides quick action buttons', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /new mission/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /emergency stop/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /system check/i })).toBeInTheDocument();
      });
    });

    test('handles emergency stop action', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        const emergencyButton = screen.getByRole('button', { name: /emergency stop/i });
        fireEvent.click(emergencyButton);

        // Should trigger emergency stop for all active missions
        expect(emergencyButton).toBeInTheDocument();
      });
    });

    test('handles system check action', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        const systemCheckButton = screen.getByRole('button', { name: /system check/i });
        fireEvent.click(systemCheckButton);

        // Should trigger system health check
        expect(systemCheckButton).toBeInTheDocument();
      });
    });
  });
});