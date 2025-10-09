import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Alert,
  Card,
  CardContent,
  Grid
} from '@mui/material';
import { Add, Edit, Delete, Refresh } from '@mui/icons-material';
import { droneApi } from '../services/ApiService';

const DroneFleet = () => {
  const [drones, setDrones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingDrone, setEditingDrone] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    capabilities: {
      camera: 'standard',
      sensors: ['gps', 'altimeter'],
      thermal: false
    },
    battery_capacity: 5000
  });

  useEffect(() => {
    loadDrones();
  }, []);

  const loadDrones = async () => {
    try {
      setLoading(true);
      const response = await droneApi.getAll();
      setDrones(response.data);
    } catch (error) {
      console.error('Error loading drones:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddDrone = () => {
    setEditingDrone(null);
    setFormData({
      name: '',
      capabilities: {
        camera: 'standard',
        sensors: ['gps', 'altimeter'],
        thermal: false
      },
      battery_capacity: 5000
    });
    setOpenDialog(true);
  };

  const handleEditDrone = (drone) => {
    setEditingDrone(drone);
    setFormData({
      name: drone.name,
      capabilities: drone.capabilities,
      battery_capacity: drone.battery_capacity
    });
    setOpenDialog(true);
  };

  const handleSaveDrone = async () => {
    try {
      if (editingDrone) {
        await droneApi.update(editingDrone.id, formData);
      } else {
        await droneApi.create(formData.name, formData.capabilities, formData.battery_capacity);
      }
      setOpenDialog(false);
      loadDrones();
    } catch (error) {
      console.error('Error saving drone:', error);
      alert('Error saving drone');
    }
  };

  const handleDeleteDrone = async (droneId) => {
    if (window.confirm('Are you sure you want to delete this drone?')) {
      try {
        await droneApi.delete(droneId);
        loadDrones();
      } catch (error) {
        console.error('Error deleting drone:', error);
        alert('Error deleting drone');
      }
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'available': return 'success';
      case 'in_mission': return 'primary';
      case 'charging': return 'warning';
      case 'maintenance': return 'default';
      case 'emergency': return 'error';
      default: return 'default';
    }
  };

  const getBatteryColor = (batteryPercent) => {
    if (batteryPercent > 50) return 'success';
    if (batteryPercent > 20) return 'warning';
    return 'error';
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Drone Fleet Management</Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadDrones}
            sx={{ mr: 1 }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={handleAddDrone}
          >
            Add Drone
          </Button>
        </Box>
      </Box>

      {/* Fleet Overview Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Drones
              </Typography>
              <Typography variant="h4">
                {drones.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Available
              </Typography>
              <Typography variant="h4" color="success.main">
                {drones.filter(d => d.status === 'available').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                In Mission
              </Typography>
              <Typography variant="h4" color="primary.main">
                {drones.filter(d => d.status === 'in_mission').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Low Battery
              </Typography>
              <Typography variant="h4" color="warning.main">
                {drones.filter(d => d.battery_percent < 30).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Drones Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Battery</TableCell>
              <TableCell>Position</TableCell>
              <TableCell>Capabilities</TableCell>
              <TableCell>Last Seen</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {drones.map((drone) => (
              <TableRow key={drone.id}>
                <TableCell>
                  <Typography variant="subtitle2">
                    {drone.name}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={drone.status}
                    color={getStatusColor(drone.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body2">
                      {drone.battery_percent}%
                    </Typography>
                    <Box
                      sx={{
                        width: 60,
                        height: 8,
                        backgroundColor: '#e0e0e0',
                        borderRadius: 1,
                        overflow: 'hidden'
                      }}
                    >
                      <Box
                        sx={{
                          width: `${drone.battery_percent}%`,
                          height: '100%',
                          backgroundColor: getBatteryColor(drone.battery_percent) === 'success' ? '#4caf50' :
                                         getBatteryColor(drone.battery_percent) === 'warning' ? '#ff9800' : '#f44336'
                        }}
                      />
                    </Box>
                  </Box>
                </TableCell>
                <TableCell>
                  {drone.current_lat && drone.current_lng ? (
                    <Typography variant="body2">
                      {drone.current_lat.toFixed(4)}, {drone.current_lng.toFixed(4)}
                    </Typography>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      Unknown
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {drone.capabilities.camera && (
                      <Chip label={drone.capabilities.camera} size="small" />
                    )}
                    {drone.capabilities.thermal && (
                      <Chip label="Thermal" size="small" color="secondary" />
                    )}
                    {drone.capabilities.sensors?.map((sensor, index) => (
                      <Chip key={index} label={sensor} size="small" variant="outlined" />
                    ))}
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {new Date(drone.last_seen).toLocaleString()}
                  </Typography>
                </TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    onClick={() => handleEditDrone(drone)}
                  >
                    <Edit />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleDeleteDrone(drone.id)}
                    color="error"
                  >
                    <Delete />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Add/Edit Drone Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingDrone ? 'Edit Drone' : 'Add New Drone'}
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Drone Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            margin="normal"
          />
          
          <FormControl fullWidth margin="normal">
            <InputLabel>Camera Type</InputLabel>
            <Select
              value={formData.capabilities.camera}
              onChange={(e) => setFormData({
                ...formData,
                capabilities: { ...formData.capabilities, camera: e.target.value }
              })}
            >
              <MenuItem value="standard">Standard</MenuItem>
              <MenuItem value="high_res">High Resolution</MenuItem>
              <MenuItem value="thermal">Thermal</MenuItem>
              <MenuItem value="night_vision">Night Vision</MenuItem>
            </Select>
          </FormControl>

          <TextField
            fullWidth
            label="Battery Capacity (mAh)"
            type="number"
            value={formData.battery_capacity}
            onChange={(e) => setFormData({ ...formData, battery_capacity: parseInt(e.target.value) })}
            margin="normal"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveDrone} variant="contained">
            {editingDrone ? 'Update' : 'Add'} Drone
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DroneFleet;