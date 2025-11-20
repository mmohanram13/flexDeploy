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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
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
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          {details.deploymentName}
        </Typography>
        <Chip
          label={details.status}
          color={getStatusColor(details.status)}
          size="large"
        />
      </Box>

      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={4}>
            <Typography variant="body2" color="text.secondary">
              Deployment ID
            </Typography>
            <Typography variant="body1">{details.deploymentId}</Typography>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Typography variant="body2" color="text.secondary">
              Status
            </Typography>
            <Chip
              label={details.status}
              color={getStatusColor(details.status)}
              size="medium"
            />
          </Grid>
          {details.timerInfo && (
            <Grid item xs={12} sm={4}>
              <Typography variant="body2" color="text.secondary">
                Current Ring
              </Typography>
              <Typography variant="body1">
                Ring {details.timerInfo.currentRing}
              </Typography>
            </Grid>
          )}
        </Grid>
        
        {details.timerInfo && details.timerInfo.nextCheckTime && (
          <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Next Gating Factor Check
            </Typography>
            <Typography variant="body1" fontWeight="bold">
              {new Date(details.timerInfo.nextCheckTime).toLocaleTimeString()}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Automated deployment progression active (30-second intervals)
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Gating Factors Section */}
      <Typography variant="h6" gutterBottom>
        Gating Factors
      </Typography>
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Monitoring frequency: 30 seconds
        </Typography>
        
        {details.gatingFactors?.gatingPrompt && (
          <Box sx={{ mb: 3, p: 2, bgcolor: 'primary.light', borderRadius: 1, borderLeft: 4, borderColor: 'primary.main' }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Gating Criteria (AI-Powered)
            </Typography>
            <Typography variant="body1" sx={{ fontStyle: 'italic' }}>
              "{details.gatingFactors.gatingPrompt}"
            </Typography>
          </Box>
        )}
        
        <Grid container spacing={2}>
          <Grid item xs={12} sm={3}>
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Avg CPU Usage Max (%)
              </Typography>
              <Typography variant="h6">
                {details.gatingFactors?.avgCpuUsageMax !== null && details.gatingFactors?.avgCpuUsageMax !== undefined
                  ? `${details.gatingFactors.avgCpuUsageMax}%` 
                  : '--'}
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Avg Memory Usage Max (%)
              </Typography>
              <Typography variant="h6">
                {details.gatingFactors?.avgMemoryUsageMax !== null && details.gatingFactors?.avgMemoryUsageMax !== undefined
                  ? `${details.gatingFactors.avgMemoryUsageMax}%` 
                  : '--'}
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Avg Disk Free Space Min (%)
              </Typography>
              <Typography variant="h6">
                {details.gatingFactors?.avgDiskFreeSpaceMin !== null && details.gatingFactors?.avgDiskFreeSpaceMin !== undefined
                  ? `${details.gatingFactors.avgDiskFreeSpaceMin}%` 
                  : '--'}
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Max Risk Score
              </Typography>
              <Typography variant="h6">
                {details.gatingFactors?.riskScoreMax !== null && details.gatingFactors?.riskScoreMax !== undefined
                  ? details.gatingFactors.riskScoreMax 
                  : '--'}
              </Typography>
            </Paper>
          </Grid>
        </Grid>
      </Paper>

      <Typography variant="h6" gutterBottom>
        Rings
      </Typography>

      {details.rings.map((ring, index) => {
        const ringId = index; // Ring 0, 1, 2, 3
        const devices = ringDevices[ringId] || [];

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
              </Grid>

              {/* Devices Table */}
              {devices.length > 0 && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
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
                                  color={device.riskScore >= 71 ? 'error' : device.riskScore >= 31 ? 'warning' : 'success'}
                                  size="small"
                                />
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Box>
                )}
            </AccordionDetails>
          </Accordion>
        );
      })}
    </Box>
  );
}
