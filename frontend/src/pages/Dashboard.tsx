import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Progress, List, Badge, Typography } from 'antd';
import { 
  RocketOutlined, 
  TeamOutlined, 
  SearchOutlined, 
  CheckCircleOutlined,
  WarningOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const { Title } = Typography;

interface DashboardStats {
  activeMissions: number;
  totalDrones: number;
  availableDrones: number;
  totalDiscoveries: number;
  confirmedDiscoveries: number;
  fleetHealth: number;
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats>({
    activeMissions: 3,
    totalDrones: 12,
    availableDrones: 8,
    totalDiscoveries: 15,
    confirmedDiscoveries: 7,
    fleetHealth: 92
  });

  const [recentActivities] = useState([
    {
      id: 1,
      type: 'mission_started',
      message: 'Mission SAR_001 started with 3 drones',
      timestamp: '2 minutes ago',
      status: 'success'
    },
    {
      id: 2,
      type: 'discovery',
      message: 'High confidence discovery detected in sector B',
      timestamp: '5 minutes ago',
      status: 'warning'
    },
    {
      id: 3,
      type: 'drone_status',
      message: 'Drone ALPHA-03 completed maintenance check',
      timestamp: '10 minutes ago',
      status: 'info'
    },
    {
      id: 4,
      type: 'mission_completed',
      message: 'Mission SAR_002 completed successfully',
      timestamp: '15 minutes ago',
      status: 'success'
    }
  ]);

  const [performanceData] = useState([
    { time: '00:00', missions: 2, discoveries: 3 },
    { time: '04:00', missions: 1, discoveries: 5 },
    { time: '08:00', missions: 3, discoveries: 8 },
    { time: '12:00', missions: 4, discoveries: 12 },
    { time: '16:00', missions: 3, discoveries: 15 },
    { time: '20:00', missions: 2, discoveries: 18 }
  ]);

  useEffect(() => {
    // Simulate real-time updates
    const interval = setInterval(() => {
      setStats(prev => ({
        ...prev,
        totalDiscoveries: prev.totalDiscoveries + Math.floor(Math.random() * 2)
      }));
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'mission_started':
      case 'mission_completed':
        return <RocketOutlined />;
      case 'discovery':
        return <SearchOutlined />;
      case 'drone_status':
        return <TeamOutlined />;
      default:
        return <ClockCircleOutlined />;
    }
  };

  const getActivityColor = (status: string) => {
    switch (status) {
      case 'success':
        return '#52c41a';
      case 'warning':
        return '#faad14';
      case 'error':
        return '#ff4d4f';
      default:
        return '#1890ff';
    }
  };

  return (
    <div>
      <Title level={2} style={{ marginBottom: '24px' }}>
        Command Dashboard
      </Title>

      {/* Statistics Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Active Missions"
              value={stats.activeMissions}
              prefix={<RocketOutlined style={{ color: '#1890ff' }} />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Available Drones"
              value={stats.availableDrones}
              suffix={`/ ${stats.totalDrones}`}
              prefix={<TeamOutlined style={{ color: '#52c41a' }} />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Discoveries"
              value={stats.totalDiscoveries}
              prefix={<SearchOutlined style={{ color: '#722ed1' }} />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Confirmed Finds"
              value={stats.confirmedDiscoveries}
              prefix={<CheckCircleOutlined style={{ color: '#faad14' }} />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        {/* Fleet Health */}
        <Col xs={24} lg={8}>
          <Card title="Fleet Health" style={{ height: '300px' }}>
            <div style={{ textAlign: 'center', padding: '20px' }}>
              <Progress
                type="circle"
                percent={stats.fleetHealth}
                strokeColor={{
                  '0%': '#108ee9',
                  '100%': '#87d068',
                }}
                format={(percent) => `${percent}%`}
              />
              <div style={{ marginTop: '16px', color: '#666' }}>
                Overall fleet operational status
              </div>
            </div>
          </Card>
        </Col>

        {/* Performance Chart */}
        <Col xs={24} lg={16}>
          <Card title="24-Hour Performance" style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="missions" 
                  stroke="#1890ff" 
                  strokeWidth={2}
                  name="Active Missions"
                />
                <Line 
                  type="monotone" 
                  dataKey="discoveries" 
                  stroke="#52c41a" 
                  strokeWidth={2}
                  name="Discoveries"
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Recent Activities */}
      <Row style={{ marginTop: '24px' }}>
        <Col span={24}>
          <Card title="Recent Activities">
            <List
              itemLayout="horizontal"
              dataSource={recentActivities}
              renderItem={item => (
                <List.Item>
                  <List.Item.Meta
                    avatar={
                      <Badge 
                        dot 
                        color={getActivityColor(item.status)}
                      >
                        <div style={{ 
                          padding: '8px', 
                          background: '#f5f5f5', 
                          borderRadius: '50%',
                          color: getActivityColor(item.status)
                        }}>
                          {getActivityIcon(item.type)}
                        </div>
                      </Badge>
                    }
                    title={item.message}
                    description={item.timestamp}
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;