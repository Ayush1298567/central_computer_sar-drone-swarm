import React, { createContext, useContext, useEffect, useState } from 'react';
import io from 'socket.io-client';

const WebSocketContext = createContext();

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

export const WebSocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    // Connect to WebSocket
    const newSocket = io('ws://localhost:8000/ws', {
      transports: ['websocket']
    });

    newSocket.on('connect', () => {
      console.log('WebSocket connected');
      setConnected(true);
    });

    newSocket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setConnected(false);
    });

    newSocket.on('telemetry', (data) => {
      setMessages(prev => [...prev, { type: 'telemetry', data, timestamp: Date.now() }]);
    });

    newSocket.on('discovery', (data) => {
      setMessages(prev => [...prev, { type: 'discovery', data, timestamp: Date.now() }]);
    });

    newSocket.on('mission_progress', (data) => {
      setMessages(prev => [...prev, { type: 'mission_progress', data, timestamp: Date.now() }]);
    });

    newSocket.on('ai_response', (data) => {
      setMessages(prev => [...prev, { type: 'ai_response', data, timestamp: Date.now() }]);
    });

    newSocket.on('command_feedback', (data) => {
      setMessages(prev => [...prev, { type: 'command_feedback', data, timestamp: Date.now() }]);
    });

    newSocket.on('battery_alert', (data) => {
      setMessages(prev => [...prev, { type: 'battery_alert', data, timestamp: Date.now() }]);
    });

    newSocket.on('collision_warning', (data) => {
      setMessages(prev => [...prev, { type: 'collision_warning', data, timestamp: Date.now() }]);
    });

    newSocket.on('significant_finding', (data) => {
      setMessages(prev => [...prev, { type: 'significant_finding', data, timestamp: Date.now() }]);
    });

    setSocket(newSocket);

    return () => {
      newSocket.close();
    };
  }, []);

  const sendMessage = (type, data) => {
    if (socket && connected) {
      socket.emit(type, data);
    }
  };

  const value = {
    socket,
    connected,
    messages,
    sendMessage
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};