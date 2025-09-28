"""
Comprehensive tests for ConversationalChat component.
Tests chat interface, message handling, AI responses, and user interactions.
"""

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ConversationalChat from '../components/mission/ConversationalChat';
import * as missionService from '../services/missionService';
import * as apiService from '../utils/api';

// Mock API services
jest.mock('../services/missionService');
jest.mock('../utils/api');

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <div>{children}</div>;
};

describe('ConversationalChat Component', () => {
  const mockMission = {
    id: 'test-mission-123',
    name: 'Test SAR Mission',
    description: 'Test mission for chat testing',
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
    drone_assignments: []
  };

  const mockChatHistory = [
    {
      id: 'msg_001',
      sender: 'user',
      content: 'Search the collapsed building for survivors',
      message_type: 'text',
      created_at: '2024-01-15T10:00:00Z'
    },
    {
      id: 'msg_002',
      sender: 'ai',
      content: 'I understand you want to search for survivors in the collapsed building. Let me help you plan this mission.',
      message_type: 'text',
      created_at: '2024-01-15T10:00:05Z'
    }
  ];

  const defaultProps = {
    mission: null,
    selectedArea: null,
    onMissionUpdate: jest.fn(),
    onAreaSelect: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();

    // Mock API responses
    (missionService.getChatHistory as jest.Mock).mockResolvedValue({
      messages: mockChatHistory
    });

    (missionService.sendChatMessage as jest.Mock).mockResolvedValue({
      success: true,
      response: 'Mission plan updated successfully',
      confidence: 0.85
    });
  });

  describe('Component Rendering', () => {
    test('renders chat interface', () => {
      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.getByText('Mission Planning Assistant')).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/describe your mission/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
    });

    test('displays chat history when mission is provided', async () => {
      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} mission={mockMission} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Search the collapsed building for survivors')).toBeInTheDocument();
        expect(screen.getByText('I understand you want to search for survivors in the collapsed building.')).toBeInTheDocument();
      });
    });

    test('shows empty state when no chat history exists', async () => {
      (missionService.getChatHistory as jest.Mock).mockResolvedValue({
        messages: []
      });

      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} mission={mockMission} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Start a conversation to plan your mission')).toBeInTheDocument();
      });
    });

    test('displays loading state while fetching chat history', () => {
      (missionService.getChatHistory as jest.Mock).mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 100))
      );

      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} mission={mockMission} />
        </TestWrapper>
      );

      expect(screen.getByText('Loading conversation...')).toBeInTheDocument();
    });
  });

  describe('User Interactions', () => {
    test('handles text input and sending messages', async () => {
      const mockOnMissionUpdate = jest.fn();

      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} onMissionUpdate={mockOnMissionUpdate} />
        </TestWrapper>
      );

      const chatInput = screen.getByPlaceholderText(/describe your mission/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      // Type a message
      fireEvent.change(chatInput, {
        target: { value: 'Search the park for missing person' }
      });

      // Send the message
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(missionService.sendChatMessage).toHaveBeenCalledWith(
          expect.objectContaining({
            content: 'Search the park for missing person',
            sender: 'user'
          })
        );
      });
    });

    test('handles Enter key to send messages', async () => {
      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} />
        </TestWrapper>
      );

      const chatInput = screen.getByPlaceholderText(/describe your mission/i);

      // Type a message and press Enter
      fireEvent.change(chatInput, {
        target: { value: 'Test message' }
      });

      fireEvent.keyDown(chatInput, { key: 'Enter' });

      await waitFor(() => {
        expect(missionService.sendChatMessage).toHaveBeenCalled();
      });
    });

    test('prevents sending empty messages', async () => {
      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} />
        </TestWrapper>
      );

      const chatInput = screen.getByPlaceholderText(/describe your mission/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      // Try to send empty message
      fireEvent.click(sendButton);

      // Should not call API
      expect(missionService.sendChatMessage).not.toHaveBeenCalled();
    });

    test('disables input during message sending', async () => {
      // Mock slow response
      (missionService.sendChatMessage as jest.Mock).mockImplementation(
        () => new Promise(resolve => setTimeout(resolve, 200))
      );

      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} />
        </TestWrapper>
      );

      const chatInput = screen.getByPlaceholderText(/describe your mission/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      // Send message
      fireEvent.change(chatInput, { target: { value: 'Test message' } });
      fireEvent.click(sendButton);

      // Input should be disabled while sending
      expect(chatInput).toBeDisabled();
      expect(sendButton).toBeDisabled();

      // Wait for completion
      await waitFor(() => {
        expect(chatInput).not.toBeDisabled();
        expect(sendButton).not.toBeDisabled();
      }, { timeout: 300 });
    });
  });

  describe('AI Response Handling', () => {
    test('displays AI responses in chat', async () => {
      const aiResponse = 'I have created a mission plan for searching the collapsed building. The estimated coverage is 85% with 2 drones.';

      (missionService.sendChatMessage as jest.Mock).mockResolvedValue({
        success: true,
        response: aiResponse,
        confidence: 0.92
      });

      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} />
        </TestWrapper>
      );

      const chatInput = screen.getByPlaceholderText(/describe your mission/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      fireEvent.change(chatInput, { target: { value: 'Plan a search mission' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText(aiResponse)).toBeInTheDocument();
      });
    });

    test('handles AI confidence scores', async () => {
      (missionService.sendChatMessage as jest.Mock).mockResolvedValue({
        success: true,
        response: 'Mission plan ready',
        confidence: 0.95
      });

      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} />
        </TestWrapper>
      );

      const chatInput = screen.getByPlaceholderText(/describe your mission/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      fireEvent.change(chatInput, { target: { value: 'Create mission' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        // High confidence should be indicated in UI
        const aiMessage = screen.getByText('Mission plan ready');
        expect(aiMessage).toBeInTheDocument();
      });
    });

    test('handles AI error responses', async () => {
      (missionService.sendChatMessage as jest.Mock).mockResolvedValue({
        success: false,
        error: 'Unable to process request'
      });

      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} />
        </TestWrapper>
      );

      const chatInput = screen.getByPlaceholderText(/describe your mission/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      fireEvent.change(chatInput, { target: { value: 'Test message' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText(/failed to send message/i)).toBeInTheDocument();
      });
    });

    test('handles AI clarification requests', async () => {
      (missionService.sendChatMessage as jest.Mock).mockResolvedValue({
        success: true,
        response: 'I need more information about the search area. Can you specify the boundaries?',
        message_type: 'question'
      });

      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} />
        </TestWrapper>
      );

      const chatInput = screen.getByPlaceholderText(/describe your mission/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      fireEvent.change(chatInput, { target: { value: 'Search somewhere' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText('I need more information about the search area.')).toBeInTheDocument();
      });
    });
  });

  describe('Mission Context Integration', () => {
    test('updates mission context when AI provides updates', async () => {
      const mockOnMissionUpdate = jest.fn();
      const updatedMission = {
        ...mockMission,
        search_altitude: 35.0,
        estimated_duration: 50
      };

      (missionService.sendChatMessage as jest.Mock).mockResolvedValue({
        success: true,
        response: 'Mission updated with new parameters',
        mission_context: updatedMission
      });

      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} onMissionUpdate={mockOnMissionUpdate} />
        </TestWrapper>
      );

      const chatInput = screen.getByPlaceholderText(/describe your mission/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      fireEvent.change(chatInput, { target: { value: 'Update altitude to 35 meters' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(mockOnMissionUpdate).toHaveBeenCalledWith(updatedMission);
      });
    });

    test('handles area selection requests from AI', async () => {
      const mockOnAreaSelect = jest.fn();

      (missionService.sendChatMessage as jest.Mock).mockResolvedValue({
        success: true,
        response: 'Please select the search area on the map',
        next_action: 'area_selection'
      });

      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} onAreaSelect={mockOnAreaSelect} />
        </TestWrapper>
      );

      const chatInput = screen.getByPlaceholderText(/describe your mission/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      fireEvent.change(chatInput, { target: { value: 'I need to search an area' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(mockOnAreaSelect).toHaveBeenCalled();
      });
    });

    test('displays mission summary when context is complete', async () => {
      const completeMission = {
        ...mockMission,
        status: 'ready',
        estimated_duration: 45,
        coverage_percentage: 85.0
      };

      (missionService.sendChatMessage as jest.Mock).mockResolvedValue({
        success: true,
        response: 'Mission is ready for approval',
        mission_context: completeMission
      });

      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} />
        </TestWrapper>
      );

      const chatInput = screen.getByPlaceholderText(/describe your mission/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      fireEvent.change(chatInput, { target: { value: 'Finalize the mission' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText('Mission is ready for approval')).toBeInTheDocument();
        expect(screen.getByText(/45.*minutes/i)).toBeInTheDocument();
        expect(screen.getByText(/85%/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    test('handles network errors gracefully', async () => {
      (missionService.sendChatMessage as jest.Mock).mockRejectedValue(
        new Error('Network error')
      );

      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} />
        </TestWrapper>
      );

      const chatInput = screen.getByPlaceholderText(/describe your mission/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      fireEvent.change(chatInput, { target: { value: 'Test message' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });
    });

    test('handles timeout errors', async () => {
      (missionService.sendChatMessage as jest.Mock).mockImplementation(
        () => new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Request timeout')), 100)
        )
      );

      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} />
        </TestWrapper>
      );

      const chatInput = screen.getByPlaceholderText(/describe your mission/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      fireEvent.change(chatInput, { target: { value: 'Test message' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(screen.getByText(/request timeout/i)).toBeInTheDocument();
      });
    });

    test('handles malformed AI responses', async () => {
      (missionService.sendChatMessage as jest.Mock).mockResolvedValue({
        success: true,
        response: null, // Malformed response
        confidence: 'invalid' // Wrong type
      });

      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} />
        </TestWrapper>
      );

      const chatInput = screen.getByPlaceholderText(/describe your mission/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      fireEvent.change(chatInput, { target: { value: 'Test message' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        // Should handle malformed response gracefully
        expect(screen.getByText(/test message/i)).toBeInTheDocument();
      });
    });
  });

  describe('Chat History Management', () => {
    test('loads and displays chat history on mount', async () => {
      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} mission={mockMission} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(missionService.getChatHistory).toHaveBeenCalledWith(mockMission.id);
        expect(screen.getByText('Search the collapsed building for survivors')).toBeInTheDocument();
      });
    });

    test('handles chat history loading errors', async () => {
      (missionService.getChatHistory as jest.Mock).mockRejectedValue(
        new Error('Failed to load chat history')
      );

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} mission={mockMission} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          'Failed to load chat history:',
          expect.any(Error)
        );
      });

      consoleSpy.mockRestore();
    });

    test('auto-scrolls to latest messages', async () => {
      // Mock long chat history
      const longHistory = Array.from({ length: 20 }, (_, i) => ({
        id: `msg_${i}`,
        sender: i % 2 === 0 ? 'user' : 'ai',
        content: `Message ${i}`,
        message_type: 'text',
        created_at: new Date(Date.now() - (20 - i) * 1000).toISOString()
      }));

      (missionService.getChatHistory as jest.Mock).mockResolvedValue({
        messages: longHistory
      });

      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} mission={mockMission} />
        </TestWrapper>
      );

      await waitFor(() => {
        // Should auto-scroll to show latest messages
        const latestMessage = screen.getByText('Message 19');
        expect(latestMessage).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA labels and roles', () => {
      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} />
        </TestWrapper>
      );

      const chatInput = screen.getByPlaceholderText(/describe your mission/i);
      expect(chatInput).toHaveAttribute('aria-label');

      const sendButton = screen.getByRole('button', { name: /send/i });
      expect(sendButton).toHaveAttribute('aria-label');
    });

    test('supports keyboard navigation', () => {
      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} />
        </TestWrapper>
      );

      const chatInput = screen.getByPlaceholderText(/describe your mission/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      // Focus management
      chatInput.focus();
      expect(document.activeElement).toBe(chatInput);

      // Tab navigation
      fireEvent.keyDown(chatInput, { key: 'Tab' });
      expect(document.activeElement).toBe(sendButton);
    });

    test('announces new messages to screen readers', async () => {
      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} />
        </TestWrapper>
      );

      const chatInput = screen.getByPlaceholderText(/describe your mission/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      fireEvent.change(chatInput, { target: { value: 'Test message' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        // New AI response should be announced
        const aiResponse = screen.getByText('Mission plan updated successfully');
        expect(aiResponse).toHaveAttribute('aria-live', 'polite');
      });
    });
  });

  describe('Performance', () => {
    test('handles large chat histories efficiently', async () => {
      // Create large chat history
      const largeHistory = Array.from({ length: 500 }, (_, i) => ({
        id: `msg_${i}`,
        sender: i % 2 === 0 ? 'user' : 'ai',
        content: `Message ${i}`,
        message_type: 'text',
        created_at: new Date(Date.now() - (500 - i) * 1000).toISOString()
      }));

      (missionService.getChatHistory as jest.Mock).mockResolvedValue({
        messages: largeHistory
      });

      const startTime = performance.now();

      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} mission={mockMission} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Message 499')).toBeInTheDocument();
      });

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Should render within reasonable time
      expect(renderTime).toBeLessThan(2000); // 2 seconds
    });

    test('debounces rapid message sending', async () => {
      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} />
        </TestWrapper>
      );

      const chatInput = screen.getByPlaceholderText(/describe your mission/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      // Rapidly send multiple messages
      for (let i = 0; i < 10; i++) {
        fireEvent.change(chatInput, { target: { value: `Message ${i}` } });
        fireEvent.click(sendButton);
      }

      // Should handle rapid inputs without issues
      await waitFor(() => {
        expect(missionService.sendChatMessage).toHaveBeenCalledTimes(10);
      });
    });
  });

  describe('Message Types', () => {
    test('handles different message types correctly', async () => {
      const messagesWithTypes = [
        {
          id: 'msg_001',
          sender: 'ai',
          content: 'Please select the search area on the map',
          message_type: 'question',
          created_at: '2024-01-15T10:00:00Z'
        },
        {
          id: 'msg_002',
          sender: 'ai',
          content: 'Mission plan is ready for approval',
          message_type: 'confirmation',
          created_at: '2024-01-15T10:01:00Z'
        }
      ];

      (missionService.getChatHistory as jest.Mock).mockResolvedValue({
        messages: messagesWithTypes
      });

      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} mission={mockMission} />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('Please select the search area on the map')).toBeInTheDocument();
        expect(screen.getByText('Mission plan is ready for approval')).toBeInTheDocument();
      });
    });

    test('displays error messages with appropriate styling', async () => {
      (missionService.sendChatMessage as jest.Mock).mockResolvedValue({
        success: false,
        error: 'Invalid mission parameters'
      });

      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} />
        </TestWrapper>
      );

      const chatInput = screen.getByPlaceholderText(/describe your mission/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      fireEvent.change(chatInput, { target: { value: 'Invalid request' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        const errorMessage = screen.getByText(/invalid mission parameters/i);
        expect(errorMessage).toBeInTheDocument();
        // Error messages should have appropriate styling
      });
    });
  });

  describe('Integration with Area Selection', () => {
    test('triggers area selection mode from AI request', async () => {
      const mockOnAreaSelect = jest.fn();

      (missionService.sendChatMessage as jest.Mock).mockResolvedValue({
        success: true,
        response: 'Please select the search area on the map',
        next_action: 'area_selection'
      });

      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} onAreaSelect={mockOnAreaSelect} />
        </TestWrapper>
      );

      const chatInput = screen.getByPlaceholderText(/describe your mission/i);
      const sendButton = screen.getByRole('button', { name: /send/i });

      fireEvent.change(chatInput, { target: { value: 'I need to define a search area' } });
      fireEvent.click(sendButton);

      await waitFor(() => {
        expect(mockOnAreaSelect).toHaveBeenCalled();
      });
    });

    test('displays selected area information', () => {
      const selectedArea = [
        [40.7128, -74.0060],
        [40.7200, -74.0060],
        [40.7200, -73.9950]
      ];

      render(
        <TestWrapper>
          <ConversationalChat {...defaultProps} selectedArea={selectedArea} />
        </TestWrapper>
      );

      // Should display area information
      expect(screen.getByText(/area selected/i)).toBeInTheDocument();
    });
  });
});