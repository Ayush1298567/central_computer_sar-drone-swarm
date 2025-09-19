import React, { useState, useRef, useEffect } from 'react';
import { 
  Card, 
  Input, 
  Button, 
  Space, 
  Typography, 
  Progress, 
  Divider,
  Row,
  Col,
  Alert,
  Spin
} from 'antd';
import { SendOutlined, RobotOutlined, UserOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Title, Text } = Typography;
const { TextArea } = Input;

interface ChatMessage {
  id: string;
  role: 'user' | 'ai';
  content: string;
  timestamp: Date;
}

interface ConversationStatus {
  state: string;
  completion_percentage: number;
  question_count: number;
  ai_confidence: number;
}

const MissionPlanning: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationStatus, setConversationStatus] = useState<ConversationStatus | null>(null);
  const [clientId] = useState(() => `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  useEffect(() => {
    // Start conversation when component mounts
    startConversation();
  }, []);

  const startConversation = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/ai/start-conversation', {
        client_id: clientId,
        initial_message: ''
      });

      if (response.data.success) {
        const aiMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'ai',
          content: response.data.ai_response,
          timestamp: new Date()
        };
        setMessages([aiMessage]);
        setConversationStatus(response.data.conversation_status);
      }
    } catch (error) {
      console.error('Failed to start conversation:', error);
      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'ai',
        content: 'Sorry, I encountered an error starting our conversation. Please try again.',
        timestamp: new Date()
      };
      setMessages([errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);

    try {
      const response = await axios.post('/api/ai/process-message', {
        client_id: clientId,
        message: inputValue
      });

      if (response.data.success) {
        const aiMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'ai',
          content: response.data.ai_response,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, aiMessage]);
        setConversationStatus(response.data.conversation_status);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        content: 'Sorry, I encountered an error processing your message. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getStateDescription = (state: string) => {
    const stateDescriptions: { [key: string]: string } = {
      'initial': 'Getting Started',
      'gathering_basic_info': 'Gathering Basic Information',
      'refining_objectives': 'Refining Mission Objectives',
      'planning_resources': 'Planning Resources',
      'safety_validation': 'Validating Safety Parameters',
      'final_review': 'Final Review',
      'completed': 'Mission Plan Complete'
    };
    return stateDescriptions[state] || 'Planning in Progress';
  };

  return (
    <div className="mission-planning-container">
      <Title level={2} style={{ marginBottom: '24px' }}>
        AI Mission Planner
      </Title>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={16}>
          <Card 
            title="Conversation with AI Planner" 
            style={{ height: '600px', display: 'flex', flexDirection: 'column' }}
            bodyStyle={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '16px' }}
          >
            {/* Chat Messages */}
            <div 
              style={{ 
                flex: 1, 
                overflowY: 'auto', 
                marginBottom: '16px',
                padding: '8px',
                border: '1px solid #f0f0f0',
                borderRadius: '4px'
              }}
            >
              {messages.map((message) => (
                <div
                  key={message.id}
                  style={{
                    marginBottom: '16px',
                    display: 'flex',
                    justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start'
                  }}
                >
                  <div
                    style={{
                      maxWidth: '80%',
                      padding: '12px 16px',
                      borderRadius: '8px',
                      backgroundColor: message.role === 'user' ? '#1890ff' : '#f0f0f0',
                      color: message.role === 'user' ? 'white' : '#333'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
                      {message.role === 'user' ? (
                        <UserOutlined style={{ marginRight: '8px' }} />
                      ) : (
                        <RobotOutlined style={{ marginRight: '8px' }} />
                      )}
                      <Text 
                        style={{ 
                          fontSize: '12px', 
                          color: message.role === 'user' ? 'rgba(255,255,255,0.8)' : '#999' 
                        }}
                      >
                        {message.role === 'user' ? 'You' : 'AI Planner'}
                      </Text>
                    </div>
                    <div style={{ whiteSpace: 'pre-wrap' }}>
                      {message.content}
                    </div>
                  </div>
                </div>
              ))}
              {loading && (
                <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: '16px' }}>
                  <div
                    style={{
                      padding: '12px 16px',
                      borderRadius: '8px',
                      backgroundColor: '#f0f0f0',
                      display: 'flex',
                      alignItems: 'center'
                    }}
                  >
                    <Spin size="small" style={{ marginRight: '8px' }} />
                    <Text>AI is thinking...</Text>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div style={{ display: 'flex', gap: '8px' }}>
              <TextArea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your response to the AI planner..."
                rows={2}
                disabled={loading}
                style={{ flex: 1 }}
              />
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={sendMessage}
                disabled={loading || !inputValue.trim()}
                size="large"
              >
                Send
              </Button>
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          {/* Planning Progress */}
          <Card title="Planning Progress" style={{ marginBottom: '16px' }}>
            {conversationStatus ? (
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <Text strong>Current Stage:</Text>
                  <br />
                  <Text>{getStateDescription(conversationStatus.state)}</Text>
                </div>
                
                <Progress 
                  percent={Math.round(conversationStatus.completion_percentage)} 
                  strokeColor={{
                    '0%': '#108ee9',
                    '100%': '#87d068',
                  }}
                />
                
                <div>
                  <Text strong>Questions Asked:</Text> {conversationStatus.question_count}
                </div>
                
                <div>
                  <Text strong>AI Confidence:</Text> {Math.round(conversationStatus.ai_confidence * 100)}%
                </div>
              </Space>
            ) : (
              <Spin />
            )}
          </Card>

          {/* Quick Tips */}
          <Card title="Planning Tips">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Alert
                message="Be Specific"
                description="Provide detailed information about the search area, target, and conditions for better mission planning."
                type="info"
                showIcon
              />
              
              <Alert
                message="Safety First"
                description="The AI will ask about weather, no-fly zones, and safety parameters to ensure safe operations."
                type="warning"
                showIcon
              />
              
              <Alert
                message="Review Carefully"
                description="Take time to review the final mission plan before approval. You can always request changes."
                type="success"
                showIcon
              />
            </Space>
          </Card>

          {/* Quick Actions */}
          <Card title="Quick Actions" style={{ marginTop: '16px' }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button block>
                Load Previous Mission Template
              </Button>
              <Button block>
                Check Weather Conditions
              </Button>
              <Button block>
                View Available Drones
              </Button>
              <Button block type="dashed">
                Save Current Progress
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default MissionPlanning;