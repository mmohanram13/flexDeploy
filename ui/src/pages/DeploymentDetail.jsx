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
                                  color={device.riskScore >= 70 ? 'success' : device.riskScore >= 31 ? 'warning' : 'error'}
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
