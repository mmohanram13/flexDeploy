import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Grid,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { useParams } from 'react-router-dom';
import { deployments, deploymentDetails } from '../data/mockData';

export default function DeploymentDetail() {
  const { id } = useParams();
  const deployment = deployments.find((d) => d.deploymentId === id);
  const details = deploymentDetails[id];

  const getStatusColor = (status) => {
    const statusColors = {
      'Not Started': 'default',
      'In Progress': 'info',
      'Completed': 'success',
      'Failed': 'error',
      'Stopped': 'warning',
    };
    return statusColors[status] || 'default';
  };

  if (!deployment || !details) {
    return (
      <Box>
        <Typography variant="h4">Deployment not found</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        {deployment.deploymentName}
      </Typography>

      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" color="text.secondary">
              Deployment ID
            </Typography>
            <Typography variant="body1">{deployment.deploymentId}</Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" color="text.secondary">
              Status
            </Typography>
            <Chip
              label={deployment.status}
              color={getStatusColor(deployment.status)}
              size="small"
            />
          </Grid>
        </Grid>
      </Paper>

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
