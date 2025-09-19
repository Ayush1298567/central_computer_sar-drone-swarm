import React from 'react';
import { Card, Typography } from 'antd';

const { Title } = Typography;

const ActiveMissions: React.FC = () => {
  return (
    <div>
      <Title level={2}>Active Missions</Title>
      <Card>
        <p>Active missions interface coming soon...</p>
      </Card>
    </div>
  );
};

export default ActiveMissions;