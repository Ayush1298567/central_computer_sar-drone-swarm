import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { webSocketService, WebSocketMessage } from '../services/websocket';

interface WebSocketContextType {
  isConnected: boolean;
  sendMessage: (type: string, data: any) => void;
  subscribe: (eventType: string, callback: (data: any) => void) => () => void;
  lastMessage: WebSocketMessage | null;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const useWebSocket = (): WebSocketContextType => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

interface WebSocketProviderProps {
  children: ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

  useEffect(() => {
    // Connect to WebSocket
    webSocketService.connect()
      .then(() => {
        setIsConnected(true);
      })
      .catch((error) => {
        console.error('Failed to connect to WebSocket:', error);
        setIsConnected(false);
      });

    // Subscribe to connection status changes
    const unsubscribe = webSocketService.subscribe('connect', () => {
      setIsConnected(true);
    });

    const unsubscribeDisconnect = webSocketService.subscribe('disconnect', () => {
      setIsConnected(false);
    });

    // Subscribe to all messages for debugging
    const unsubscribeMessage = webSocketService.subscribe('*', (data) => {
      setLastMessage({
        type: 'message',
        data,
        timestamp: new Date().toISOString(),
      });
    });

    return () => {
      unsubscribe();
      unsubscribeDisconnect();
      unsubscribeMessage();
      webSocketService.disconnect();
    };
  }, []);

  const sendMessage = (type: string, data: any) => {
    webSocketService.sendMessage(type, data);
  };

  const subscribe = (eventType: string, callback: (data: any) => void) => {
    return webSocketService.subscribe(eventType, callback);
  };

  const value: WebSocketContextType = {
    isConnected,
    sendMessage,
    subscribe,
    lastMessage,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};
