import React from 'react';
import { Layout, Badge, Button, Space, Typography } from 'antd';
import { BellOutlined, AlertOutlined, WifiOutlined } from '@ant-design/icons';
import { useWebSocket } from '../../contexts/WebSocketContext';

const { Header: AntHeader } = Layout;
const { Text } = Typography;

const Header: React.FC = () => {
  const { connected } = useWebSocket();

  return (
    <AntHeader 
      style={{ 
        position: 'fixed', 
        zIndex: 1, 
        width: '100%',
        paddingLeft: '216px', // Account for sidebar width
        background: '#fff',
        borderBottom: '1px solid #f0f0f0',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}
    >
      <div>
        <Text strong style={{ fontSize: '18px', color: '#1890ff' }}>
          SAR Drone Command Center
        </Text>
      </div>
      
      <Space size="large">
        {/* Connection Status */}
        <Space>
          <WifiOutlined style={{ color: connected ? '#52c41a' : '#ff4d4f' }} />
          <Text style={{ color: connected ? '#52c41a' : '#ff4d4f' }}>
            {connected ? 'Connected' : 'Disconnected'}
          </Text>
        </Space>

        {/* Emergency Alerts */}
        <Badge count={2} size="small">
          <Button 
            type="text" 
            icon={<AlertOutlined />}
            className="emergency-button"
            size="large"
          />
        </Badge>

        {/* Notifications */}
        <Badge count={5} size="small">
          <Button 
            type="text" 
            icon={<BellOutlined />}
            size="large"
          />
        </Badge>
      </Space>
    </AntHeader>
  );
};

export default Header;