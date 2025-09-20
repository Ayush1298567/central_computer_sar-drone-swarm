import { useEffect, useRef, useCallback } from 'react';
import { webSocketService, WebSocketEventHandler } from '../services/websocket';

export function useWebSocket() {
  const handlersRef = useRef<Map<string, WebSocketEventHandler>>(new Map());

  const subscribe = useCallback((event: string, handler: WebSocketEventHandler) => {
    // Remove existing handler if any
    const existingHandler = handlersRef.current.get(event);
    if (existingHandler) {
      webSocketService.off(event, existingHandler);
    }

    // Add new handler
    webSocketService.on(event, handler);
    handlersRef.current.set(event, handler);
  }, []);

  const unsubscribe = useCallback((event: string) => {
    const handler = handlersRef.current.get(event);
    if (handler) {
      webSocketService.off(event, handler);
      handlersRef.current.delete(event);
    }
  }, []);

  const emit = useCallback((event: string, data: any) => {
    if (event === 'drone_command') {
      webSocketService.sendDroneCommand(data.droneId, data.command);
    } else if (event === 'chat_message') {
      webSocketService.sendChatMessage(data.sessionId, data.message);
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      handlersRef.current.forEach((handler, event) => {
        webSocketService.off(event, handler);
      });
      handlersRef.current.clear();
    };
  }, []);

  return {
    subscribe,
    unsubscribe,
    emit,
    isConnected: webSocketService.isConnected(),
    subscribeMission: webSocketService.subscribeMission.bind(webSocketService),
    unsubscribeMission: webSocketService.unsubscribeMission.bind(webSocketService),
    subscribeDrone: webSocketService.subscribeDrone.bind(webSocketService),
    unsubscribeDrone: webSocketService.unsubscribeDrone.bind(webSocketService),
    subscribeChatSession: webSocketService.subscribeChatSession.bind(webSocketService),
    unsubscribeChatSession: webSocketService.unsubscribeChatSession.bind(webSocketService),
  };
}

export default useWebSocket;