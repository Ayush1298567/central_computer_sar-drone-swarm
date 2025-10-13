import React, { createContext, useContext, useEffect, useRef, useState, ReactNode } from 'react';
import wsServiceDefault, { wsService as legacyWsService } from '../services/websocket';

interface WebSocketContextType {
  isConnected: boolean;
  subscribe: (topic: string, handler: (payload: any) => void) => () => void;
  unsubscribe: (topic: string, handler: (payload: any) => void) => void;
  send: (data: any) => void;
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
  const service = legacyWsService || wsServiceDefault;
  const disposersRef = useRef(new Map<string, Map<Function, Function>>());

  useEffect(() => {
    service.connect();
    setIsConnected(service.getConnectionStatus() === 'connected');

    return () => {
      service.disconnect();
    };
  }, []);

  const subscribe = (topic: string, handler: (payload: any) => void) => {
    const disposer = service.on(topic, handler);
    let topicMap = disposersRef.current.get(topic);
    if (!topicMap) {
      topicMap = new Map();
      disposersRef.current.set(topic, topicMap);
    }
    topicMap.set(handler, disposer);
    return () => {
      disposer();
      topicMap?.delete(handler);
    };
  };
  const unsubscribe = (topic: string, handler: (payload: any) => void) => {
    const topicMap = disposersRef.current.get(topic);
    const disposer = topicMap?.get(handler);
    if (disposer) {
      disposer();
      topicMap?.delete(handler);
    }
  };
  const send = (data: any) => service.send(data);

  const value: WebSocketContextType = {
    isConnected,
    subscribe,
    unsubscribe,
    send,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};
