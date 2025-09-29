import React, { createContext, useContext, useEffect, useState } from 'react';
import { api } from '../../utils/api';

interface WebSocketContextType {
  isConnected: boolean;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  sendMessage: (message: any) => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

interface WebSocketProviderProps {
  children: React.ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const [socket, setSocket] = useState<WebSocket | null>(null);

  useEffect(() => {
    // Initialize WebSocket connection
    const connectWebSocket = () => {
      try {
        setConnectionStatus('connecting');
        const wsUrl = api.websocket.system();
        const newSocket = new WebSocket(wsUrl);

        newSocket.onopen = () => {
          setIsConnected(true);
          setConnectionStatus('connected');
          console.log('WebSocket connected');
        };

        newSocket.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            console.log('WebSocket message received:', message);
            // Handle incoming messages here
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        newSocket.onclose = () => {
          setIsConnected(false);
          setConnectionStatus('disconnected');
          console.log('WebSocket disconnected');
          // Attempt to reconnect after 5 seconds
          setTimeout(connectWebSocket, 5000);
        };

        newSocket.onerror = (error) => {
          setConnectionStatus('error');
          console.error('WebSocket error:', error);
        };

        setSocket(newSocket);
      } catch (error) {
        setConnectionStatus('error');
        console.error('WebSocket connection error:', error);
      }
    };

    connectWebSocket();

    // Cleanup on unmount
    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, []);

  const sendMessage = (message: any) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  };

  const value: WebSocketContextType = {
    isConnected,
    connectionStatus,
    sendMessage,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = (): WebSocketContextType => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};