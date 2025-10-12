import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Button,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  LinearProgress,
  Stepper,
  Step,
  StepLabel,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  PlayArrow as PlayArrowIcon,
  Stop as StopIcon,
  ArrowBack as ArrowBackIcon,
  CheckCircle as CheckCircleIcon,
  Pause as PauseIcon,
  RadioButtonUnchecked as RadioButtonUncheckedIcon,
} from '@mui/icons-material';
import { deploymentDetails } from '../data/mockData';

const getRingIcon = (status) => {
  switch (status) {
    case 'completed':
      return <CheckCircleIcon color="success" />;
    case 'paused':
      return <PauseIcon color="warning" />;
    case 'pending':
      return <RadioButtonUncheckedIcon color="disabled" />;
    default:
      return <RadioButtonUncheckedIcon />;
  }
};

const getStatusColor = (status) => {
  switch (status) {
    case 'completed':
      return 'success';
    case 'paused':
      return 'warning';
    case 'in-progress':
      return 'info';
    case 'pending':
      return 'default';
    default:
      return 'default';
  }
};

export default function DeploymentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const deployment = deploymentDetails[id];

  if (!deployment) {
    return (
      <Box>
        <Typography variant="h5">Deployment not found</Typography>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/deployments')}>
          Back to Deployments
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Button
        startIcon={<ArrowBackIcon />}
        onClick={() => navigate('/deployments')}
        sx={{ mb: 2 }}
      >
        Back to Deployments
      </Button>

      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h4" gutterBottom>
              Deployment: {deployment.name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Started: {new Date(deployment.startTime).toLocaleString()}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <Chip
              label={deployment.status === 'paused' ? '🟡 Paused' : deployment.status === 'complete' ? '✅ Complete' : '⏳ In Progress'}
              color={getStatusColor(deployment.status)}
            />
            {deployment.status === 'paused' && (
              <>
                <Button variant="contained" color="success" startIcon={<PlayArrowIcon />}>
                  Resume
                </Button>
                <Button variant="outlined" color="error" startIcon={<StopIcon />}>
                  Stop
                </Button>
              </>
            )}
          </Box>
        </Box>
      </Paper>

      {/* Progress Flow */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Progress Flow
        </Typography>
        <Stepper activeStep={deployment.rings.findIndex(r => r.status === 'paused' || r.status === 'in-progress')} alternativeLabel>
          {deployment.rings.map((ring) => (
            <Step key={ring.id} completed={ring.status === 'completed'}>
              <StepLabel
                StepIconComponent={() => getRingIcon(ring.status)}
              >
                Ring {ring.id}: {ring.name}
              </StepLabel>
            </Step>
          ))}
        </Stepper>
      </Paper>

      {/* Ring Details */}
      {deployment.rings.map((ring) => (
        <Accordion key={ring.id} defaultExpanded={ring.status !== 'pending'} sx={{ mb: 2 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
              {getRingIcon(ring.status)}
              <Typography variant="h6">
                Ring {ring.id}: {ring.name}
              </Typography>
              {ring.status === 'paused' && (
                <Chip label="⚠️ PAUSED BY AI" color="warning" size="small" />
              )}
              {ring.status === 'completed' && (
                <Chip label="✓ Completed" color="success" size="small" />
              )}
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Box>
              {/* Status Info */}
              <Box sx={{ mb: 2 }}>
                <Typography variant="body1" gutterBottom>
                  <strong>Status:</strong>{' '}
                  {ring.status === 'completed' ? '✓ Completed' : ring.status === 'paused' ? '🟡 Paused' : '⏸️ Waiting'}
                  {ring.deployed ? ` | ${ring.successful}/${ring.deployed} devices deployed` : ` | ${ring.successful}/${ring.devices} devices successful`}
                </Typography>
                {ring.duration && (
                  <Typography variant="body1">
                    <strong>Duration:</strong> {ring.duration}
                  </Typography>
                )}
                {ring.startTime && (
                  <Typography variant="body1">
                    <strong>Started:</strong> {ring.startTime}
                    {ring.endTime && ` | Completed: ${ring.endTime}`}
                  </Typography>
                )}
              </Box>

              {/* AI Reasoning for Paused Ring */}
              {ring.status === 'paused' && ring.aiReasoning && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  <Typography variant="body1" fontWeight={600} gutterBottom>
                    🚨 AI Decision: Deployment paused automatically
                  </Typography>
                  <Typography variant="body2" sx={{ fontStyle: 'italic', mb: 1 }}>
                    🤖 Reasoning:
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 2 }}>
                    "{ring.aiReasoning}"
                  </Typography>
                  
                  {ring.affectedDevices && ring.affectedDevices.length > 0 && (
                    <>
                      <Typography variant="body2" fontWeight={600} gutterBottom>
                        Affected Devices:
                      </Typography>
                      <TableContainer>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Device Name</TableCell>
                              <TableCell>Status</TableCell>
                              <TableCell>Anomaly</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {ring.affectedDevices.map((device, idx) => (
                              <TableRow key={idx}>
                                <TableCell>{device.name}</TableCell>
                                <TableCell>⚠️</TableCell>
                                <TableCell>{device.anomaly}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </>
                  )}
                  
                  <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
                    <Button variant="contained" color="warning" startIcon={<PlayArrowIcon />} size="small">
                      Override and Continue
                    </Button>
                    <Button variant="outlined" color="error" startIcon={<StopIcon />} size="small">
                      Stop Deployment
                    </Button>
                  </Box>
                </Alert>
              )}

              {/* AI Insight */}
              {ring.aiInsight && ring.status !== 'paused' && (
                <Alert severity={ring.status === 'completed' ? 'success' : 'info'} sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    <strong>🤖 AI Insights:</strong> {ring.aiInsight}
                  </Typography>
                </Alert>
              )}

              {/* Device Details Table */}
              {ring.deviceDetails && ring.deviceDetails.length > 0 && (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Device Name</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Start</TableCell>
                        <TableCell>End</TableCell>
                        <TableCell>Duration</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {ring.deviceDetails.map((device, idx) => (
                        <TableRow key={idx}>
                          <TableCell>{device.name}</TableCell>
                          <TableCell>{device.status === 'success' ? '✓' : '✗'}</TableCell>
                          <TableCell>{device.startTime}</TableCell>
                          <TableCell>{device.endTime}</TableCell>
                          <TableCell>{device.duration}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </Box>
          </AccordionDetails>
        </Accordion>
      ))}
    </Box>
  );
}
