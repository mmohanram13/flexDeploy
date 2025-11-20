import React, { useState, useEffect } from 'react';
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
  Button,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormControl,
  FormLabel,
  Grid,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../api/client';

export default function Deployments() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [deployments, setDeployments] = useState([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [newDeployment, setNewDeployment] = useState({
    deploymentName: '',
    gatingFactorMode: 'default', // 'default', 'custom', or 'prompt'
    customGatingFactors: {
      avgCpuUsageMax: 100,
      avgMemoryUsageMax: 100,
      avgDiskFreeSpaceMin: 0,
    },
    gatingPrompt: '',
  });

  useEffect(() => {
    fetchDeployments();
  }, []);

  // Polling effect - poll every 5 seconds if any deployment is In Progress
  useEffect(() => {
    const hasActiveDeployments = deployments.some(
      (d) => d.status === 'In Progress'
    );

    if (!hasActiveDeployments) {
      return; // No active deployments, don't poll
    }

    const intervalId = setInterval(() => {
      fetchDeployments();
    }, 5000); // Poll every 5 seconds

    // Cleanup interval on unmount or when dependencies change
    return () => clearInterval(intervalId);
  }, [deployments]);

  const fetchDeployments = async () => {
    try {
      const data = await apiClient.getDeployments();
      setDeployments(data);
    } catch (error) {
      console.error('Error fetching deployments:', error);
    } finally {
      setLoading(false);
    }
  };

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

  const handleRunDeployment = async (deploymentId) => {
    try {
      await apiClient.runDeployment(deploymentId);
      fetchDeployments();
    } catch (error) {
      console.error('Error running deployment:', error);
    }
  };

  const handleStopDeployment = async (deploymentId) => {
    try {
      await apiClient.stopDeployment(deploymentId);
      fetchDeployments();
    } catch (error) {
      console.error('Error stopping deployment:', error);
    }
  };

  const handleDeleteDeployment = async (deploymentId) => {
    if (!window.confirm('Are you sure you want to delete this deployment? This action cannot be undone.')) {
      return;
    }

    try {
      await apiClient.deleteDeployment(deploymentId);
      fetchDeployments();
    } catch (error) {
      console.error('Error deleting deployment:', error);
      alert('Failed to delete deployment.');
    }
  };

  const handleOpenDialog = () => {
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setNewDeployment({
      deploymentName: '',
      gatingFactorMode: 'default',
      customGatingFactors: {
        avgCpuUsageMax: 100,
        avgMemoryUsageMax: 100,
        avgDiskFreeSpaceMin: 0,
      },
      gatingPrompt: '',
    });
  };

  const handleCreateDeployment = async () => {
    if (!newDeployment.deploymentName) {
      alert('Please provide a deployment name');
      return;
    }

    if (newDeployment.gatingFactorMode === 'prompt' && !newDeployment.gatingPrompt) {
      alert('Please provide a gating factor prompt');
      return;
    }

    try {
      const deploymentData = {
        deploymentName: newDeployment.deploymentName,
        status: 'Not Started',
        gatingFactorMode: newDeployment.gatingFactorMode,
      };

      if (newDeployment.gatingFactorMode === 'custom') {
        deploymentData.customGatingFactors = newDeployment.customGatingFactors;
      } else if (newDeployment.gatingFactorMode === 'prompt') {
        deploymentData.gatingPrompt = newDeployment.gatingPrompt;
      }

      await apiClient.createDeployment(deploymentData);
      handleCloseDialog();
      fetchDeployments();
    } catch (error) {
      console.error('Error creating deployment:', error);
      alert('Failed to create deployment.');
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Deployments
        </Typography>
        <Button
          variant="contained"
          color="primary"
          size="large"
          onClick={handleOpenDialog}
        >
          Create Deployment
        </Button>
      </Box>

      <TableContainer component={Paper} elevation={2}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Deployment ID</TableCell>
              <TableCell>Deployment Name</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {deployments.map((deployment) => (
              <TableRow key={deployment.deploymentId} hover>
                <TableCell>{deployment.deploymentId}</TableCell>
                <TableCell>{deployment.deploymentName}</TableCell>
                <TableCell>
                  <Chip
                    label={deployment.status}
                    color={getStatusColor(deployment.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell align="right">
                  <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                    {deployment.status === 'In Progress' ? (
                      <Button
                        variant="outlined"
                        size="small"
                        color="error"
                        onClick={() => handleStopDeployment(deployment.deploymentId)}
                      >
                        Stop Deployment
                      </Button>
                    ) : (
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => handleRunDeployment(deployment.deploymentId)}
                      >
                        Run Deployment
                      </Button>
                    )}
                    <Button
                      variant="contained"
                      size="small"
                      onClick={() => navigate(`/deployments/${deployment.deploymentId}`)}
                    >
                      View Details
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      color="error"
                      onClick={() => handleDeleteDeployment(deployment.deploymentId)}
                    >
                      Delete
                    </Button>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create Deployment Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>Create New Deployment</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 2 }}>
            <TextField
              label="Deployment Name"
              value={newDeployment.deploymentName}
              onChange={(e) => setNewDeployment({ ...newDeployment, deploymentName: e.target.value })}
              placeholder="Windows Security Update KB5043146"
              fullWidth
              required
            />

            <FormControl component="fieldset">
              <FormLabel component="legend">Gating Factors Configuration</FormLabel>
              <RadioGroup
                value={newDeployment.gatingFactorMode}
                onChange={(e) => setNewDeployment({ ...newDeployment, gatingFactorMode: e.target.value })}
              >
                <FormControlLabel
                  value="default"
                  control={<Radio />}
                  label="Use Default Gating Factors"
                />
                <FormControlLabel
                  value="custom"
                  control={<Radio />}
                  label="Provide Custom Gating Factors"
                />
                <FormControlLabel
                  value="prompt"
                  control={<Radio />}
                  label="Generate from Prompt (AI-powered)"
                />
              </RadioGroup>
            </FormControl>

            {newDeployment.gatingFactorMode === 'custom' && (
              <Paper elevation={1} sx={{ p: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Custom Gating Factors
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <TextField
                    label="Avg CPU Usage Max (%)"
                    type="number"
                    value={newDeployment.customGatingFactors.avgCpuUsageMax}
                    onChange={(e) => setNewDeployment({
                      ...newDeployment,
                      customGatingFactors: {
                        ...newDeployment.customGatingFactors,
                        avgCpuUsageMax: parseFloat(e.target.value) || 0
                      }
                    })}
                    inputProps={{ min: 0, max: 100 }}
                    fullWidth
                  />
                  <TextField
                    label="Avg Memory Usage Max (%)"
                    type="number"
                    value={newDeployment.customGatingFactors.avgMemoryUsageMax}
                    onChange={(e) => setNewDeployment({
                      ...newDeployment,
                      customGatingFactors: {
                        ...newDeployment.customGatingFactors,
                        avgMemoryUsageMax: parseFloat(e.target.value) || 0
                      }
                    })}
                    inputProps={{ min: 0, max: 100 }}
                    fullWidth
                  />
                  <TextField
                    label="Avg Disk Free Space Min (%)"
                    type="number"
                    value={newDeployment.customGatingFactors.avgDiskFreeSpaceMin}
                    onChange={(e) => setNewDeployment({
                      ...newDeployment,
                      customGatingFactors: {
                        ...newDeployment.customGatingFactors,
                        avgDiskFreeSpaceMin: parseFloat(e.target.value) || 0
                      }
                    })}
                    inputProps={{ min: 0, max: 100 }}
                    fullWidth
                  />
                </Box>
              </Paper>
            )}

            {newDeployment.gatingFactorMode === 'prompt' && (
              <TextField
                label="Gating Factor Prompt"
                value={newDeployment.gatingPrompt}
                onChange={(e) => setNewDeployment({ ...newDeployment, gatingPrompt: e.target.value })}
                placeholder="e.g., 'Only proceed to next ring if average CPU usage is below 60% and memory usage is below 70%'"
                multiline
                rows={3}
                fullWidth
                required
                helperText="Describe your desired gating criteria in natural language. AI will analyze device metrics against this prompt to determine whether to proceed to the next ring."
              />
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleCreateDeployment} variant="contained" color="primary">
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
