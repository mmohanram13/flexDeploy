import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Button,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  RadioGroup,
  FormControlLabel,
  Radio,
  Stepper,
  Step,
  StepLabel,
} from '@mui/material';
import {
  PlayArrow as PlayArrowIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import { deployments } from '../data/mockData';

const getStatusColor = (status) => {
  switch (status) {
    case 'paused':
      return 'warning';
    case 'in-progress':
      return 'info';
    case 'complete':
      return 'success';
    case 'failed':
      return 'error';
    default:
      return 'default';
  }
};

const getStatusIcon = (status) => {
  switch (status) {
    case 'paused':
      return '🟡';
    case 'in-progress':
      return '⏳';
    case 'complete':
      return '✅';
    case 'failed':
      return '❌';
    default:
      return '';
  }
};

export default function Deployments() {
  const navigate = useNavigate();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [deploymentForm, setDeploymentForm] = useState({
    name: '',
    packageId: '',
    targetDevices: 'all',
    strategy: 'default',
  });

  const steps = ['Deployment Details', 'Configure Strategy', 'Review & Schedule'];

  const handleViewDeployment = (deploymentId) => {
    navigate(`/deployments/${deploymentId}`);
  };

  const handleNext = () => {
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleCreateDeployment = () => {
    // This would normally send data to backend
    console.log('Creating deployment:', deploymentForm);
    setCreateDialogOpen(false);
    setActiveStep(0);
    setDeploymentForm({
      name: '',
      packageId: '',
      targetDevices: 'all',
      strategy: 'default',
    });
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Deployments</Typography>
        <Button
          variant="contained"
          startIcon={<span>+</span>}
          onClick={() => setCreateDialogOpen(true)}
        >
          Create Deployment
        </Button>
      </Box>

      <TableContainer component={Paper} elevation={2}>
        <Table>
          <TableHead>
            <TableRow sx={{ bgcolor: 'grey.100' }}>
              <TableCell sx={{ fontWeight: 600 }}>Deployment ID</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Deployment Name</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Progress</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Current Ring</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Start Time</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {deployments.map((deployment) => (
              <TableRow key={deployment.id} hover>
                <TableCell>
                  <Typography
                    variant="body2"
                    sx={{ cursor: 'pointer', color: 'primary.main', textDecoration: 'underline' }}
                    onClick={() => handleViewDeployment(deployment.id)}
                  >
                    {deployment.id}
                  </Typography>
                </TableCell>
                <TableCell>{deployment.name}</TableCell>
                <TableCell>
                  <Chip
                    label={`${getStatusIcon(deployment.status)} ${deployment.status.charAt(0).toUpperCase() + deployment.status.slice(1)}`}
                    color={getStatusColor(deployment.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={deployment.progress}
                      sx={{ width: 100 }}
                    />
                    <Typography variant="body2">{deployment.progress}%</Typography>
                  </Box>
                </TableCell>
                <TableCell>{deployment.currentRing}</TableCell>
                <TableCell>
                  {new Date(deployment.startTime).toLocaleString('en-US', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    {deployment.status === 'paused' && (
                      <IconButton size="small" color="success">
                        <PlayArrowIcon />
                      </IconButton>
                    )}
                    <IconButton
                      size="small"
                      color="primary"
                      onClick={() => handleViewDeployment(deployment.id)}
                    >
                      <AssessmentIcon />
                    </IconButton>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create Deployment Dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Create New Deployment</DialogTitle>
        <DialogContent>
          <Stepper activeStep={activeStep} sx={{ mb: 4, mt: 2 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          {/* Step 1: Deployment Details */}
          {activeStep === 0 && (
            <Box>
              <TextField
                fullWidth
                label="Deployment Name"
                value={deploymentForm.name}
                onChange={(e) => setDeploymentForm({ ...deploymentForm, name: e.target.value })}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Package/Patch ID"
                value={deploymentForm.packageId}
                onChange={(e) => setDeploymentForm({ ...deploymentForm, packageId: e.target.value })}
                sx={{ mb: 2 }}
              />
              <Typography variant="body1" gutterBottom>
                Target Devices:
              </Typography>
              <RadioGroup
                value={deploymentForm.targetDevices}
                onChange={(e) => setDeploymentForm({ ...deploymentForm, targetDevices: e.target.value })}
              >
                <FormControlLabel value="all" control={<Radio />} label="All Devices (324)" />
                <FormControlLabel value="sites" control={<Radio />} label="Specific Sites" />
                <FormControlLabel value="departments" control={<Radio />} label="Specific Departments" />
              </RadioGroup>
            </Box>
          )}

          {/* Step 2: Configure Strategy */}
          {activeStep === 1 && (
            <Box>
              <Typography variant="body1" gutterBottom>
                How would you like to configure this deployment?
              </Typography>
              <RadioGroup
                value={deploymentForm.strategy}
                onChange={(e) => setDeploymentForm({ ...deploymentForm, strategy: e.target.value })}
              >
                <FormControlLabel
                  value="default"
                  control={<Radio />}
                  label="Use Default Rings (AI-assigned cohorts)"
                />
                <Typography variant="body2" color="text.secondary" sx={{ ml: 4, mb: 2 }}>
                  Devices will be deployed according to their current ring assignments (5 rings, 324 devices)
                </Typography>
                <FormControlLabel
                  value="custom"
                  control={<Radio />}
                  label="Customize with AI Chat"
                />
                <Typography variant="body2" color="text.secondary" sx={{ ml: 4 }}>
                  Describe your strategy and AI will configure it
                </Typography>
              </RadioGroup>
            </Box>
          )}

          {/* Step 3: Review & Schedule */}
          {activeStep === 2 && (
            <Box>
              <Paper sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
                <Typography variant="h6" gutterBottom>
                  Deployment Summary
                </Typography>
                <Typography variant="body2">
                  <strong>Name:</strong> {deploymentForm.name || 'Not specified'}
                </Typography>
                <Typography variant="body2">
                  <strong>Package:</strong> {deploymentForm.packageId || 'Not specified'}
                </Typography>
                <Typography variant="body2">
                  <strong>Target:</strong> {deploymentForm.targetDevices === 'all' ? '324 devices across 5 rings' : deploymentForm.targetDevices}
                </Typography>
              </Paper>

              <Typography variant="h6" gutterBottom>
                Schedule:
              </Typography>
              <RadioGroup defaultValue="immediate">
                <FormControlLabel value="immediate" control={<Radio />} label="Start immediately" />
                <FormControlLabel value="scheduled" control={<Radio />} label="Schedule for:" />
              </RadioGroup>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          {activeStep > 0 && <Button onClick={handleBack}>Back</Button>}
          {activeStep < steps.length - 1 ? (
            <Button variant="contained" onClick={handleNext}>
              Next
            </Button>
          ) : (
            <Button variant="contained" onClick={handleCreateDeployment}>
              Create Deployment
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
}
