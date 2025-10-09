import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box, AppBar, Toolbar, Typography, Tabs, Tab, Container } from '@mui/material';
import MissionPlanning from './components/MissionPlanning';
import DroneFleet from './components/DroneFleet';
import MissionControl from './components/MissionControl';
import { WebSocketProvider } from './services/WebSocketService';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function App() {
  const [currentTab, setCurrentTab] = useState(0);

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <WebSocketProvider>
        <Box sx={{ flexGrow: 1 }}>
          <AppBar position="static">
            <Toolbar>
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                SAR Drone Central Computer System
              </Typography>
            </Toolbar>
          </AppBar>
          
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={currentTab} onChange={handleTabChange} aria-label="main navigation">
              <Tab label="Mission Planning" />
              <Tab label="Drone Fleet" />
              <Tab label="Mission Control" />
            </Tabs>
          </Box>

          <TabPanel value={currentTab} index={0}>
            <MissionPlanning />
          </TabPanel>
          
          <TabPanel value={currentTab} index={1}>
            <DroneFleet />
          </TabPanel>
          
          <TabPanel value={currentTab} index={2}>
            <MissionControl />
          </TabPanel>
        </Box>
      </WebSocketProvider>
    </ThemeProvider>
  );
}

export default App;