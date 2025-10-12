import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  Grid,
  Divider,
} from '@mui/material';

export default function Settings() {
  const [settings, setSettings] = useState({
    devicePool: 324,
    refreshInterval: 30,
    aiModel: 'Amazon Nova Act / Qwen3-4B-Chat',
    riskRecalcInterval: 5,
    cpuDeviation: 20,
    memorySpike: 30,
    diskErrors: 5,
  });

  const handleSave = () => {
    console.log('Saving settings:', settings);
    // This would normally send data to backend
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      {/* SuperOps Simulation Configuration */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          SuperOps Simulation Configuration
        </Typography>
        <Divider sx={{ mb: 2 }} />
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="number"
              label="Simulated Device Pool"
              value={settings.devicePool}
              onChange={(e) => setSettings({ ...settings, devicePool: parseInt(e.target.value) })}
              helperText="Number of devices in the simulation"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="number"
              label="Data Refresh Interval (seconds)"
              value={settings.refreshInterval}
              onChange={(e) => setSettings({ ...settings, refreshInterval: parseInt(e.target.value) })}
              helperText="How often to refresh device data"
            />
          </Grid>
          <Grid item xs={12}>
            <Button variant="outlined" size="large">
              Reload Simulated Data
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* AI Configuration */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          AI Configuration
        </Typography>
        <Divider sx={{ mb: 2 }} />
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Model"
              value={settings.aiModel}
              onChange={(e) => setSettings({ ...settings, aiModel: e.target.value })}
              helperText="AI model used for risk assessment and decision making"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="number"
              label="Risk Recalculation Interval (minutes)"
              value={settings.riskRecalcInterval}
              onChange={(e) => setSettings({ ...settings, riskRecalcInterval: parseInt(e.target.value) })}
              helperText="How often to recalculate device risk scores"
            />
          </Grid>
          <Grid item xs={12}>
            <Button variant="outlined" size="large">
              Trigger Manual Recalculation
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Default Anomaly Thresholds */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Default Anomaly Thresholds
        </Typography>
        <Divider sx={{ mb: 2 }} />
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              type="number"
              label="CPU Deviation (%)"
              value={settings.cpuDeviation}
              onChange={(e) => setSettings({ ...settings, cpuDeviation: parseInt(e.target.value) })}
              helperText="Default CPU deviation threshold"
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              type="number"
              label="Memory Spike (%)"
              value={settings.memorySpike}
              onChange={(e) => setSettings({ ...settings, memorySpike: parseInt(e.target.value) })}
              helperText="Default memory spike threshold"
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              type="number"
              label="Disk I/O Errors (per hour)"
              value={settings.diskErrors}
              onChange={(e) => setSettings({ ...settings, diskErrors: parseInt(e.target.value) })}
              helperText="Default disk error threshold"
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Save Button */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
        <Button variant="contained" size="large" onClick={handleSave}>
          Save Settings
        </Button>
      </Box>
    </Box>
  );
}
