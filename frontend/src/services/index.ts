// Services Index
// Central export point for all API services

export * from './api';
export * from './missionService';
export * from './droneService';
export * from './chatService';
export * from './analyticsService';
export * from './testApiEndpoints';

// Service initialization function
import { missionService } from './missionService';
import { droneService } from './droneService';
import { chatService } from './chatService';
import { analyticsService } from './analyticsService';
import { useQueryClient } from '@tanstack/react-query';

export const initializeServices = (queryClient: ReturnType<typeof useQueryClient>) => {
  // Set query client for all services that need it
  missionService.setQueryClient(queryClient);
  droneService.setQueryClient(queryClient);
  chatService.setQueryClient(queryClient);
  analyticsService.setQueryClient(queryClient);

  console.log('API Services initialized successfully');
};

// Service health check
export const checkAllServices = async (): Promise<{
  api: boolean;
  mission: boolean;
  drone: boolean;
  chat: boolean;
  analytics: boolean;
}> => {
  const results = {
    api: false,
    mission: false,
    drone: false,
    chat: false,
    analytics: false,
  };

  try {
    // Check API health
    const { checkApiHealth } = await import('./api');
    results.api = await checkApiHealth();

    // Check each service with a simple request
    if (results.api) {
      try {
        await missionService.getMissions(1, 1);
        results.mission = true;
      } catch (error) {
        console.warn('Mission service check failed:', error);
      }

      try {
        await droneService.getDrones();
        results.drone = true;
      } catch (error) {
        console.warn('Drone service check failed:', error);
      }

      try {
        const { chatService } = await import('./chatService');
        await chatService.getConversations(1, 1);
        results.chat = true;
      } catch (error) {
        console.warn('Chat service check failed:', error);
      }

      try {
        await analyticsService.getMissionAnalytics('1d');
        results.analytics = true;
      } catch (error) {
        console.warn('Analytics service check failed:', error);
      }
    }
  } catch (error) {
    console.error('Service health check failed:', error);
  }

  return results;
};