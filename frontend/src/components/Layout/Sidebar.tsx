import React from 'react';
import { Layout, Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  RocketOutlined,
  PlayCircleOutlined,
  TeamOutlined,
  MonitorOutlined,
  BulbOutlined
} from '@ant-design/icons';

const { Sider } = Layout;

const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: 'Dashboard'
    },
    {
      key: '/mission-planning',
      icon: <RocketOutlined />,
      label: 'Mission Planning'
    },
    {
      key: '/active-missions',
      icon: <PlayCircleOutlined />,
      label: 'Active Missions'
    },
    {
      key: '/drone-fleet',
      icon: <TeamOutlined />,
      label: 'Drone Fleet'
    },
    {
      key: '/monitoring',
      icon: <MonitorOutlined />,
      label: 'Real-time Monitoring'
    },
    {
      key: '/ai-insights',
      icon: <BulbOutlined />,
      label: 'AI Insights'
    }
  ];

  const handleMenuClick = (key: string) => {
    navigate(key);
  };

  return (
    <Sider
      collapsible
      theme="dark"
      style={{
        overflow: 'auto',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
      }}
    >
      <div className="logo">
        SAR Command
      </div>
      <Menu
        theme="dark"
        selectedKeys={[location.pathname]}
        mode="inline"
        items={menuItems}
        onClick={({ key }) => handleMenuClick(key)}
      />
    </Sider>
  );
};

export default Sidebar;