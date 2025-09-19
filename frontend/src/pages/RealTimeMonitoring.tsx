import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Typography, Badge, Button, Space, List } from 'antd';
import { PlayCircleOutlined, PauseCircleOutlined, StopOutlined } from '@ant-design/icons';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import { useWebSocket } from '../contexts/WebSocketContext';
import 'leaflet/dist/leaflet.css';

const { Title, Text } = Typography;

interface DronePosition {
  id: string;
  name: string;
  position: [number, number];
  status: string;
  battery: number;
  altitude: number;
}

const RealTimeMonitoring: React.FC = () => {
  const { socket, connected } = useWebSocket();
  const [drones, setDrones] = useState<DronePosition[]>([
    {
      id: 'DRONE_001',
      name: 'Alpha-1',
      position: [37.7749, -122.4194],
      status: 'active',
      battery: 78,
      altitude: 100
    },
    {
      id: 'DRONE_002', 
      name: 'Alpha-2',
      position: [37.7849, -122.4094],
      status: 'active',
      battery: 82,
      altitude: 95
    }
  ]);

  const [selectedDrone, setSelectedDrone] = useState<string | null>(null);
  const [videoStream, setVideoStream] = useState<boolean>(false);

  useEffect(() => {
    if (socket && connected) {
      // Subscribe to real-time updates
      socket.on('drone_telemetry', (data) => {
        setDrones(prev => 
          prev.map(drone => 
            drone.id === data.drone_id 
              ? { ...drone, position: [data.location.latitude, data.location.longitude], battery: data.power.battery_percentage }
              : drone
          )
        );
      });

      socket.on('mission_status', (data) => {
        console.log('Mission status update:', data);
      });

      return () => {
        socket.off('drone_telemetry');
        socket.off('mission_status');
      };
    }
  }, [socket, connected]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return '#52c41a';
      case 'idle': return '#faad14';
      case 'offline': return '#ff4d4f';
      case 'maintenance': return '#722ed1';
      default: return '#d9d9d9';
    }
  };

  const handleDroneSelect = (droneId: string) => {
    setSelectedDrone(droneId);
    if (socket && connected) {
      socket.emit('subscribe_drone_telemetry', { drone_id: droneId });
    }
  };

  const toggleVideoStream = () => {
    setVideoStream(!videoStream);
    if (selectedDrone && socket && connected) {
      if (!videoStream) {
        socket.emit('start_video_stream', { drone_id: selectedDrone });
      } else {
        socket.emit('stop_video_stream', { drone_id: selectedDrone });
      }
    }
  };

  const selectedDroneData = drones.find(d => d.id === selectedDrone);

  return (
    <div>
      <Title level={2} style={{ marginBottom: '24px' }}>
        Real-time Monitoring
      </Title>

      <Row gutter={[16, 16]}>
        {/* Map View */}
        <Col xs={24} lg={16}>
          <Card title="Live Mission Map" style={{ height: '500px' }}>
            <MapContainer
              center={[37.7749, -122.4194]}
              zoom={13}
              style={{ height: '400px', width: '100%' }}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              />
              {drones.map((drone) => (
                <Marker 
                  key={drone.id} 
                  position={drone.position}
                  eventHandlers={{
                    click: () => handleDroneSelect(drone.id)
                  }}
                >
                  <Popup>
                    <div>
                      <strong>{drone.name}</strong><br />
                      Status: <Badge color={getStatusColor(drone.status)} text={drone.status} /><br />
                      Battery: {drone.battery}%<br />
                      Altitude: {drone.altitude}m
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </Card>
        </Col>

        {/* Drone List */}
        <Col xs={24} lg={8}>
          <Card title="Active Drones" style={{ height: '500px' }}>
            <List
              itemLayout="horizontal"
              dataSource={drones}
              renderItem={drone => (
                <List.Item
                  style={{ 
                    cursor: 'pointer',
                    background: selectedDrone === drone.id ? '#f0f0f0' : 'transparent',
                    padding: '8px',
                    borderRadius: '4px'
                  }}
                  onClick={() => handleDroneSelect(drone.id)}
                >
                  <List.Item.Meta
                    avatar={
                      <Badge 
                        color={getStatusColor(drone.status)} 
                        text=""
                      />
                    }
                    title={drone.name}
                    description={
                      <Space direction="vertical" size="small">
                        <Text>Status: {drone.status}</Text>
                        <Text>Battery: {drone.battery}%</Text>
                        <Text>Alt: {drone.altitude}m</Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      {/* Drone Details Panel */}
      {selectedDroneData && (
        <Row style={{ marginTop: '16px' }}>
          <Col xs={24} lg={12}>
            <Card title={`${selectedDroneData.name} - Telemetry`}>
              <Row gutter={[16, 8]}>
                <Col span={12}>
                  <Text strong>Position:</Text>
                  <br />
                  <Text>{selectedDroneData.position[0].toFixed(6)}, {selectedDroneData.position[1].toFixed(6)}</Text>
                </Col>
                <Col span={12}>
                  <Text strong>Battery:</Text>
                  <br />
                  <Text>{selectedDroneData.battery}%</Text>
                </Col>
                <Col span={12}>
                  <Text strong>Altitude:</Text>
                  <br />
                  <Text>{selectedDroneData.altitude}m</Text>
                </Col>
                <Col span={12}>
                  <Text strong>Status:</Text>
                  <br />
                  <Badge color={getStatusColor(selectedDroneData.status)} text={selectedDroneData.status} />
                </Col>
              </Row>
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            <Card 
              title="Video Stream" 
              extra={
                <Space>
                  <Button 
                    type={videoStream ? "default" : "primary"}
                    icon={<PlayCircleOutlined />}
                    onClick={toggleVideoStream}
                    disabled={!connected}
                  >
                    {videoStream ? 'Stop' : 'Start'} Stream
                  </Button>
                </Space>
              }
            >
              <div 
                style={{
                  height: '200px',
                  background: videoStream ? '#000' : '#f0f0f0',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: videoStream ? 'white' : '#999',
                  borderRadius: '4px'
                }}
              >
                {videoStream ? (
                  <div>
                    <PlayCircleOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                    <br />
                    Live Video Stream
                    <br />
                    <Text style={{ color: 'rgba(255,255,255,0.7)', fontSize: '12px' }}>
                      {selectedDroneData.name} - 1080p @ 30fps
                    </Text>
                  </div>
                ) : (
                  <div>
                    <Text>Video stream not active</Text>
                    <br />
                    <Text type="secondary">Click "Start Stream" to begin</Text>
                  </div>
                )}
              </div>
            </Card>
          </Col>
        </Row>
      )}
    </div>
  );
};

export default RealTimeMonitoring;