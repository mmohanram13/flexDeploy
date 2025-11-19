import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Grid,
  CircularProgress,
  Button,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  Snackbar,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { useParams } from 'react-router-dom';
import { apiClient } from '../api/client';

export default function DeploymentDetail() {
  const { id } = useParams();
  const [loading, setLoading] = useState(true);
  const [details, setDetails] = useState(null);
  const [ringDevices, setRingDevices] = useState({});
  const [expandedRing, setExpandedRing] = useState(null);
  
  // Simulation controls state
  const [simulationValues, setSimulationValues] = useState({});
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  const fetchDeploymentDetail = async () => {
    try {
      const data = await apiClient.getDeploymentDetail(id);
      setDetails(data);
    } catch (error) {
      console.error('Error fetching deployment details:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRingDevices = async (ringId) => {
    try {
      const data = await apiClient.getRingDevices(id, ringId);
      setRingDevices(prev => ({
        ...prev,
        [ringId]: data.devices
      }));
    } catch (error) {
      console.error(`Error fetching devices for ring ${ringId}:`, error);
    }
  };

  useEffect(() => {
    fetchDeploymentDetail();
  }, [id]);

  // Polling effect - poll every 5 seconds if any ring is in Started or In Progress state
  useEffect(() => {
    if (!details || !details.rings) {
      return;
    }

    const hasActiveRings = details.rings.some(
      (ring) => ring.status === 'Started' || ring.status === 'In Progress'
    );

    if (!hasActiveRings) {
      return; // No active rings, don't poll
    }

    const intervalId = setInterval(() => {
      fetchDeploymentDetail();
      // Refresh devices for expanded rings
      Object.keys(ringDevices).forEach(ringId => {
        fetchRingDevices(parseInt(ringId));
      });
    }, 5000); // Poll every 5 seconds

    // Cleanup interval on unmount or when dependencies change
    return () => clearInterval(intervalId);
  }, [details, id, ringDevices]);

  const handleAccordionChange = (ringId) => (event, isExpanded) => {
    setExpandedRing(isExpanded ? ringId : null);
    if (isExpanded && !ringDevices[ringId]) {
      fetchRingDevices(ringId);
    }
  };

  const handleSimulationChange = (ringId, field, value) => {
    setSimulationValues(prev => ({
      ...prev,
      [ringId]: {
        ...prev[ringId],
        [field]: value
      }
    }));
  };

  const handleApplySimulation = async (ringId) => {
    const values = simulationValues[ringId] || {};
    
    try {
      const payload = {
        ringId: ringId,
        deploymentId: id,
      };

      // Add only the fields that have values
      if (values.avgCpuUsage !== undefined && values.avgCpuUsage !== '') {
        payload.avgCpuUsage = parseFloat(values.avgCpuUsage);
      }
      if (values.avgMemoryUsage !== undefined && values.avgMemoryUsage !== '') {
        payload.avgMemoryUsage = parseFloat(values.avgMemoryUsage);
      }
      if (values.avgDiskSpace !== undefined && values.avgDiskSpace !== '') {
        payload.avgDiskSpace = parseFloat(values.avgDiskSpace);
      }
      if (values.riskScore !== undefined && values.riskScore !== '') {
        payload.riskScore = parseInt(values.riskScore);
      }

      await apiClient.updateRingMetrics(payload);
      
      // Refresh devices for this ring
      await fetchRingDevices(ringId);
      
      setSnackbar({
        open: true,
        message: `Successfully updated metrics for Ring ${ringId}`,
        severity: 'success'
      });
    } catch (error) {
      console.error('Error applying simulation:', error);
      setSnackbar({
        open: true,
        message: `Failed to update metrics: ${error.message}`,
        severity: 'error'
      });
    }
  };

  const getStatusColor = (status) => {
    const statusColors = {
      'Not Started': 'default',
      'Started': 'primary',
      'In Progress': 'info',
      'Completed': 'success',
      'Failed': 'error',
      'Stopped': 'warning',
    };
    return statusColors[status] || 'default';
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!details) {
    return (
      <Box>
        <Typography variant="h4">Deployment not found</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        {details.deploymentName}
      </Typography>

      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" color="text.secondary">
              Deployment ID
            </Typography>
            <Typography variant="body1">{details.deploymentId}</Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* Gating Factors Section */}
      {details.gatingFactors && (
        <>
          <Typography variant="h6" gutterBottom>
            Gating Factors
          </Typography>
          <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={4}>
                <Typography variant="body2" color="text.secondary">
                  Avg CPU Usage Max
                </Typography>
                <Typography variant="body1">
                  {details.gatingFactors.avgCpuUsageMax !== null 
                    ? `${details.gatingFactors.avgCpuUsageMax}%` 
                    : '--'}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Typography variant="body2" color="text.secondary">
                  Avg Memory Usage Max
                </Typography>
                <Typography variant="body1">
                  {details.gatingFactors.avgMemoryUsageMax !== null 
                    ? `${details.gatingFactors.avgMemoryUsageMax}%` 
                    : '--'}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Typography variant="body2" color="text.secondary">
                  Avg Disk Free Space Min
                </Typography>
                <Typography variant="body1">
                  {details.gatingFactors.avgDiskFreeSpaceMin !== null 
                    ? `${details.gatingFactors.avgDiskFreeSpaceMin}%` 
                    : '--'}
                </Typography>
              </Grid>
            </Grid>
          </Paper>
        </>
      )}

      <Typography variant="h6" gutterBottom>
        Rings
      </Typography>

      {details.rings.map((ring, index) => {
        const ringId = index; // Ring 0, 1, 2, 3
        const devices = ringDevices[ringId] || [];
        const simValues = simulationValues[ringId] || {};

        return (
          <Accordion 
            key={ring.ringName} 
            elevation={2} 
            sx={{ mb: 1 }}
            expanded={expandedRing === ringId}
            onChange={handleAccordionChange(ringId)}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                <Typography sx={{ flexGrow: 1 }}>{ring.ringName}</Typography>
                <Chip
                  label={ring.status}
                  color={getStatusColor(ring.status)}
                  size="small"
                />
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Number of Devices
                  </Typography>
                  <Typography variant="body1">{ring.deviceCount}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Status
                  </Typography>
                  <Chip
                    label={ring.status}
                    color={getStatusColor(ring.status)}
                    size="small"
                  />
                </Grid>
                {ring.failureReason && (
                  <Grid item xs={12}>
                    <Typography variant="body2" color="text.secondary">
                      Failure Reason
                    </Typography>
                    <Typography variant="body1" color="error">
                      {ring.failureReason}
                    </Typography>
                  </Grid>
                )}

                {/* Simulation Controls */}
                <Grid item xs={12}>
                  <Paper elevation={1} sx={{ p: 2, mt: 2, bgcolor: 'action.hover' }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Simulation Controls
                    </Typography>
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
                      Set average metrics for all devices in this ring
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={3}>
                        <TextField
                          label="Avg CPU Usage (%)"
                          type="number"
                          size="small"
                          fullWidth
                          value={simValues.avgCpuUsage || ''}
                          onChange={(e) => handleSimulationChange(ringId, 'avgCpuUsage', e.target.value)}
                          inputProps={{ min: 0, max: 100, step: 0.1 }}
                        />
                      </Grid>
                      <Grid item xs={12} sm={3}>
                        <TextField
                          label="Avg Memory Usage (%)"
                          type="number"
                          size="small"
                          fullWidth
                          value={simValues.avgMemoryUsage || ''}
                          onChange={(e) => handleSimulationChange(ringId, 'avgMemoryUsage', e.target.value)}
                          inputProps={{ min: 0, max: 100, step: 0.1 }}
                        />
                      </Grid>
                      <Grid item xs={12} sm={3}>
                        <TextField
                          label="Avg Disk Usage (%)"
                          type="number"
                          size="small"
                          fullWidth
                          value={simValues.avgDiskSpace || ''}
                          onChange={(e) => handleSimulationChange(ringId, 'avgDiskSpace', e.target.value)}
                          inputProps={{ min: 0, max: 100, step: 0.1 }}
                        />
                      </Grid>
                      <Grid item xs={12} sm={3}>
                        <Button
                          variant="contained"
                          fullWidth
                          onClick={() => handleApplySimulation(ringId)}
                          sx={{ height: '40px' }}
                        >
                          Apply
                        </Button>
                      </Grid>
                    </Grid>
                  </Paper>
                </Grid>

                {/* Devices Table */}
                {devices.length > 0 && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                      Devices in this Ring
                    </Typography>
                    <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 400 }}>
                      <Table size="small" stickyHeader>
                        <TableHead>
                          <TableRow>
                            <TableCell>Device ID</TableCell>
                            <TableCell>Device Name</TableCell>
                            <TableCell align="right">CPU Usage</TableCell>
                            <TableCell align="right">Memory Usage</TableCell>
                            <TableCell align="right">Disk Usage</TableCell>
                            <TableCell align="right">Risk Score</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {devices.map((device) => (
                            <TableRow key={device.deviceId}>
                              <TableCell>{device.deviceId}</TableCell>
                              <TableCell>{device.deviceName}</TableCell>
                              <TableCell align="right">{device.avgCpuUsage.toFixed(1)}%</TableCell>
                              <TableCell align="right">{device.avgMemoryUsage.toFixed(1)}%</TableCell>
                              <TableCell align="right">{device.avgDiskSpace.toFixed(1)}%</TableCell>
                              <TableCell align="right">
                                <Chip 
                                  label={device.riskScore}
                                  color={device.riskScore >= 70 ? 'success' : device.riskScore >= 31 ? 'warning' : 'error'}
                                  size="small"
                                />
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Grid>
                )}
              </Grid>
            </AccordionDetails>
          </Accordion>
        );
      })}

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert onClose={() => setSnackbar({ ...snackbar, open: false })} severity={snackbar.severity}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
