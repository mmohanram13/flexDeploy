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
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { useParams } from 'react-router-dom';
import { apiClient } from '../api/client';

export default function DeploymentDetail() {
  const { id } = useParams();
  const [loading, setLoading] = useState(true);
  const [details, setDetails] = useState(null);

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
    }, 5000); // Poll every 5 seconds

    // Cleanup interval on unmount or when dependencies change
    return () => clearInterval(intervalId);
  }, [details, id]);

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

      {details.rings.map((ring) => (
        <Accordion key={ring.ringName} elevation={2} sx={{ mb: 1 }}>
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
          </AccordionDetails>
        </Accordion>
      ))}
    </Box>
  );
}
