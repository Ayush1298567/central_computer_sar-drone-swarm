import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import io, { Socket } from 'socket.io-client';

interface WebSocketContextType {
  socket: Socket | null;
  connected: boolean;
  sendMessage: (event: string, data: any) => void;
  joinRoom: (room: string) => void;
  leaveRoom: (room: string) => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const useWebSocket = () => {
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
  const [socket, setSocket] = useState<Socket | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // Initialize WebSocket connection
    const newSocket = io('ws://localhost:8000', {
      transports: ['websocket'],
      autoConnect: true
    });

    newSocket.on('connect', () => {
      console.log('WebSocket connected');
      setConnected(true);
    });

    newSocket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setConnected(false);
    });

    newSocket.on('error', (error) => {
      console.error('WebSocket error:', error);
    });

    setSocket(newSocket);

    return () => {
      newSocket.close();
    };
  }, []);

  const sendMessage = (event: string, data: any) => {
    if (socket && connected) {
      socket.emit(event, data);
    }
  };

  const joinRoom = (room: string) => {
    if (socket && connected) {
      socket.emit('join_room', { room });
    }
  };

  const leaveRoom = (room: string) => {
    if (socket && connected) {
      socket.emit('leave_room', { room });
    }
  };

  const value = {
    socket,
    connected,
    sendMessage,
    joinRoom,
    leaveRoom
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};