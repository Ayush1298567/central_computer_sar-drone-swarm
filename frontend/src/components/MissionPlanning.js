import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  Divider,
  Chip
} from '@mui/material';
import { Send, PlayArrow, Pause, Stop } from '@mui/icons-material';
import { useWebSocket } from '../services/WebSocketService';
import { planningApi } from '../services/ApiService';

const MissionPlanning = () => {
  const [sessionId, setSessionId] = useState(null);
  const [missionDescription, setMissionDescription] = useState('');
  const [conversation, setConversation] = useState([]);
  const [currentResponse, setCurrentResponse] = useState('');
  const [isPlanning, setIsPlanning] = useState(false);
  const [planningStatus, setPlanningStatus] = useState(null);
  const [missionPlan, setMissionPlan] = useState(null);
  const { sendMessage } = useWebSocket();

  useEffect(() => {
    // Listen for AI responses
    const handleMessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'ai_response') {
        setConversation(prev => [...prev, {
          type: 'assistant',
          content: data.data.message || data.data.question,
          timestamp: new Date()
        }]);
      }
    };

    // Note: In a real implementation, you'd listen to WebSocket messages here
    // For now, we'll simulate the conversation flow
  }, []);

  const startMissionPlanning = async () => {
    if (!missionDescription.trim()) {
      alert('Please enter a mission description');
      return;
    }

    try {
      setIsPlanning(true);
      const newSessionId = `session_${Date.now()}`;
      setSessionId(newSessionId);
      
      // Add user message to conversation
      setConversation(prev => [...prev, {
        type: 'user',
        content: missionDescription,
        timestamp: new Date()
      }]);

      // Start planning
      const response = await planningApi.start(missionDescription, newSessionId);
      
      // Simulate AI questions (in real implementation, these come from WebSocket)
      setTimeout(() => {
        setConversation(prev => [...prev, {
          type: 'assistant',
          content: 'Where exactly is this search area located? Please provide coordinates or address.',
          timestamp: new Date()
        }]);
      }, 1000);

      setTimeout(() => {
        setConversation(prev => [...prev, {
          type: 'assistant',
          content: 'How large is the search area approximately?',
          timestamp: new Date()
        }]);
      }, 3000);

      setTimeout(() => {
        setConversation(prev => [...prev, {
          type: 'assistant',
          content: 'Are there any known hazards in the area?',
          timestamp: new Date()
        }]);
      }, 5000);

    } catch (error) {
      console.error('Error starting mission planning:', error);
      alert('Error starting mission planning');
    }
  };

  const sendResponse = async () => {
    if (!currentResponse.trim() || !sessionId) return;

    try {
      // Add user response to conversation
      setConversation(prev => [...prev, {
        type: 'user',
        content: currentResponse,
        timestamp: new Date()
      }]);

      // Send response to API
      await planningApi.respond(sessionId, currentResponse);
      
      setCurrentResponse('');

      // Simulate AI response (in real implementation, this comes from WebSocket)
      setTimeout(() => {
        setConversation(prev => [...prev, {
          type: 'assistant',
          content: 'Thank you for that information. Let me ask one more question: How many drones would you like to deploy for this mission?',
          timestamp: new Date()
        }]);
      }, 1000);

      // Simulate mission plan generation
      setTimeout(() => {
        setMissionPlan({
          mission_name: 'SAR Mission - ' + missionDescription.substring(0, 30),
          search_area: {
            type: 'Polygon',
            coordinates: [[
              [-122.5, 37.7], [-122.4, 37.7], 
              [-122.4, 37.8], [-122.5, 37.8], 
              [-122.5, 37.7]
            ]]
          },
          drone_assignments: [
            { drone_id: 1, zone: 'northwest', waypoints: 25 },
            { drone_id: 2, zone: 'northeast', waypoints: 30 },
            { drone_id: 3, zone: 'southwest', waypoints: 28 }
          ],
          estimated_duration: 120,
          safety_parameters: {
            min_battery: 30,
            max_altitude: 100
          }
        });
        setIsPlanning(false);
      }, 5000);

    } catch (error) {
      console.error('Error sending response:', error);
      alert('Error sending response');
    }
  };

  const acceptMission = () => {
    if (missionPlan) {
      alert('Mission plan accepted! You can now start the mission from the Mission Control tab.');
    }
  };

  return (
    <Box sx={{ display: 'flex', gap: 2, height: 'calc(100vh - 120px)' }}>
      {/* Conversation Panel */}
      <Paper sx={{ flex: 1, p: 2, display: 'flex', flexDirection: 'column' }}>
        <Typography variant="h6" gutterBottom>
          Mission Planning Conversation
        </Typography>
        
        {!sessionId ? (
          <Box>
            <TextField
              fullWidth
              multiline
              rows={4}
              label="Describe your SAR mission"
              value={missionDescription}
              onChange={(e) => setMissionDescription(e.target.value)}
              placeholder="e.g., Search the collapsed warehouse for survivors"
              sx={{ mb: 2 }}
            />
            <Button
              variant="contained"
              startIcon={<PlayArrow />}
              onClick={startMissionPlanning}
              disabled={!missionDescription.trim()}
            >
              Start Mission Planning
            </Button>
          </Box>
        ) : (
          <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            {/* Conversation Messages */}
            <Box sx={{ flex: 1, overflow: 'auto', mb: 2, p: 1, border: '1px solid #e0e0e0', borderRadius: 1 }}>
              {conversation.map((message, index) => (
                <Box
                  key={index}
                  sx={{
                    mb: 1,
                    p: 1,
                    borderRadius: 1,
                    backgroundColor: message.type === 'user' ? '#e3f2fd' : '#f5f5f5',
                    textAlign: message.type === 'user' ? 'right' : 'left'
                  }}
                >
                  <Typography variant="body2" color="text.secondary">
                    {message.type === 'user' ? 'You' : 'AI Assistant'}
                  </Typography>
                  <Typography variant="body1">
                    {message.content}
                  </Typography>
                </Box>
              ))}
              {isPlanning && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <LinearProgress sx={{ flex: 1 }} />
                  <Typography variant="body2">AI is thinking...</Typography>
                </Box>
              )}
            </Box>

            {/* Response Input */}
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField
                fullWidth
                value={currentResponse}
                onChange={(e) => setCurrentResponse(e.target.value)}
                placeholder="Type your response..."
                onKeyPress={(e) => e.key === 'Enter' && sendResponse()}
                disabled={isPlanning}
              />
              <Button
                variant="contained"
                startIcon={<Send />}
                onClick={sendResponse}
                disabled={!currentResponse.trim() || isPlanning}
              >
                Send
              </Button>
            </Box>
          </Box>
        )}
      </Paper>

      {/* Mission Plan Panel */}
      <Paper sx={{ width: 400, p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Mission Plan
        </Typography>
        
        {!missionPlan ? (
          <Typography color="text.secondary">
            Complete the conversation to generate a mission plan
          </Typography>
        ) : (
          <Box>
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {missionPlan.mission_name}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Estimated Duration: {missionPlan.estimated_duration} minutes
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Drone Assignments: {missionPlan.drone_assignments.length} drones
                </Typography>
              </CardContent>
            </Card>

            <Typography variant="subtitle1" gutterBottom>
              Drone Assignments
            </Typography>
            <List dense>
              {missionPlan.drone_assignments.map((assignment, index) => (
                <ListItem key={index}>
                  <ListItemText
                    primary={`Drone ${assignment.drone_id}`}
                    secondary={`Zone: ${assignment.zone} • ${assignment.waypoints} waypoints`}
                  />
                </ListItem>
              ))}
            </List>

            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle1" gutterBottom>
              Safety Parameters
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              <Chip label={`Min Battery: ${missionPlan.safety_parameters.min_battery}%`} size="small" />
              <Chip label={`Max Altitude: ${missionPlan.safety_parameters.max_altitude}m`} size="small" />
            </Box>

            <Box sx={{ mt: 2 }}>
              <Button
                variant="contained"
                fullWidth
                onClick={acceptMission}
                startIcon={<PlayArrow />}
              >
                Accept Mission Plan
              </Button>
            </Box>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default MissionPlanning;