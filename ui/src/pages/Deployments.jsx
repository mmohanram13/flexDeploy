import React from 'react';
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
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { deployments } from '../data/mockData';

export default function Deployments() {
  const navigate = useNavigate();

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

  const handleRunDeployment = (deploymentId) => {
    // TODO: Implement deployment run logic
    console.log('Running deployment:', deploymentId);
  };

  const handleStopDeployment = (deploymentId) => {
    // TODO: Implement deployment stop logic
    console.log('Stopping deployment:', deploymentId);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Deployments
      </Typography>

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
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
