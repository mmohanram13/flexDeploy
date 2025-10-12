import React, { useState } from 'react';
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
  Drawer,
  Card,
  CardContent,
  Grid,
  Button,
  TextField,
  MenuItem,
  Divider,
} from '@mui/material';
import { Visibility as VisibilityIcon } from '@mui/icons-material';
import { devices, rings } from '../data/mockData';

const getRingColor = (ringId) => {
  const ring = rings.find((r) => r.id === ringId);
  return ring ? ring.color : '#757575';
};

export default function Devices() {
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const handleViewDevice = (device) => {
    setSelectedDevice(device);
    setDrawerOpen(true);
  };

  const handleCloseDrawer = () => {
    setDrawerOpen(false);
    setSelectedDevice(null);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Devices
      </Typography>

      <TableContainer component={Paper} elevation={2}>
        <Table>
          <TableHead>
            <TableRow sx={{ bgcolor: 'grey.100' }}>
              <TableCell sx={{ fontWeight: 600 }}>Device ID</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Device Name</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Manufacturer</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Model</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>OS Name</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Site</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Department</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Current Ring</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Risk Score</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {devices.map((device) => (
              <TableRow key={device.id} hover>
                <TableCell>{device.id}</TableCell>
                <TableCell>{device.name}</TableCell>
                <TableCell>{device.manufacturer}</TableCell>
                <TableCell>{device.model}</TableCell>
                <TableCell>{device.osName}</TableCell>
                <TableCell>{device.site}</TableCell>
                <TableCell>{device.department}</TableCell>
                <TableCell>
                  <Chip
                    label={`Ring ${device.ring} (${device.ringName})`}
                    size="small"
                    sx={{
                      bgcolor: getRingColor(device.ring),
                      color: 'white',
                      fontWeight: 600,
                    }}
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="body2" fontWeight={600}>
                    {device.riskScore}
                  </Typography>
                </TableCell>
                <TableCell>
                  <IconButton
                    size="small"
                    color="primary"
                    onClick={() => handleViewDevice(device)}
                  >
                    <VisibilityIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Device Detail Drawer */}
      <Drawer
        anchor="right"
        open={drawerOpen}
        onClose={handleCloseDrawer}
        sx={{
          '& .MuiDrawer-paper': {
            width: { xs: '100%', sm: 600 },
            p: 3,
          },
        }}
      >
        {selectedDevice && (
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h5">Device: {selectedDevice.name}</Typography>
              <Button onClick={handleCloseDrawer}>×</Button>
            </Box>

            {/* Hardware Profile */}
            <Card sx={{ mb: 3 }} elevation={1}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Hardware Profile
                </Typography>
                <Typography variant="body2" gutterBottom>
                  <strong>CPU:</strong> {selectedDevice.cpu.model} | {selectedDevice.cpu.cores} @ {selectedDevice.cpu.speed}
                </Typography>
                <Typography variant="body2" gutterBottom>
                  <strong>RAM:</strong> {selectedDevice.memory.total} | <strong>Disk:</strong> {selectedDevice.disk.total}
                </Typography>
                <Typography variant="body2">
                  <strong>Network:</strong> {selectedDevice.network.ip} ({selectedDevice.network.mac})
                </Typography>
              </CardContent>
            </Card>

            {/* Performance Snapshot */}
            <Card sx={{ mb: 3 }} elevation={1}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Performance Snapshot
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2">
                      <strong>CPU Usage:</strong> {selectedDevice.cpu.usage}%
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2">
                      <strong>RAM Usage:</strong> {selectedDevice.memory.usage}%
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2">
                      <strong>Disk Usage:</strong> {selectedDevice.disk.usage}%
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2">
                      <strong>Active:</strong> Normal
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>

            {/* Current Ring Assignment */}
            <Card sx={{ mb: 3 }} elevation={1}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Current Ring Assignment
                </Typography>
                <Box sx={{ bgcolor: 'grey.100', p: 2, borderRadius: 1, mb: 2 }}>
                  <Typography variant="body1" fontWeight={600} gutterBottom>
                    <Chip
                      label={`Ring ${selectedDevice.ring}: ${selectedDevice.ringName}`}
                      size="small"
                      sx={{
                        bgcolor: getRingColor(selectedDevice.ring),
                        color: 'white',
                        fontWeight: 600,
                        mr: 1,
                      }}
                    />
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>Risk Score:</strong> {selectedDevice.riskScore}
                  </Typography>
                  <Divider sx={{ my: 1 }} />
                  <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                    🤖 AI Reasoning:
                  </Typography>
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    "{selectedDevice.aiReasoning}"
                  </Typography>
                </Box>
              </CardContent>
            </Card>

            {/* Manual Override */}
            <Card sx={{ mb: 3 }} elevation={1}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Manual Override (Optional)
                </Typography>
                <TextField
                  select
                  fullWidth
                  label="Move to Ring"
                  defaultValue={selectedDevice.ring}
                  sx={{ mb: 2 }}
                  size="small"
                >
                  {rings.map((ring) => (
                    <MenuItem key={ring.id} value={ring.id}>
                      Ring {ring.id}: {ring.name}
                    </MenuItem>
                  ))}
                </TextField>
                <TextField
                  fullWidth
                  label="Reason"
                  multiline
                  rows={2}
                  sx={{ mb: 2 }}
                  size="small"
                />
                <Button variant="contained" size="small">
                  Override Assignment
                </Button>
              </CardContent>
            </Card>

            {/* Deployment History */}
            <Card elevation={1}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Deployment History
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Deploy ID</TableCell>
                        <TableCell>Name</TableCell>
                        <TableCell>Ring</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Date</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {selectedDevice.deploymentHistory.map((deploy) => (
                        <TableRow key={deploy.id}>
                          <TableCell>{deploy.id}</TableCell>
                          <TableCell>{deploy.name}</TableCell>
                          <TableCell>{deploy.ring}</TableCell>
                          <TableCell>
                            {deploy.status === 'success' ? '✓' : '✗'}
                          </TableCell>
                          <TableCell>{deploy.date}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Box>
        )}
      </Drawer>
    </Box>
  );
}
