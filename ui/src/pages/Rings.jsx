import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Button,
  CircularProgress,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { apiClient } from '../api/client';

export default function Rings() {
  const [loading, setLoading] = useState(true);
  const [rings, setRings] = useState([]);
  const [gatingFactors, setGatingFactors] = useState({
    avgCpuUsageMax: 100,
    avgMemoryUsageMax: 100,
    avgDiskFreeSpaceMin: 0,
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [ringsData, gatingData] = await Promise.all([
        apiClient.getRings(),
        apiClient.getGatingFactors(),
      ]);
      setRings(ringsData);
      setGatingFactors(gatingData);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePromptChange = (ringId, value) => {
    setRings((prevRings) =>
      prevRings.map((ring) =>
        ring.ringId === ringId ? { ...ring, categorizationPrompt: value } : ring
      )
    );
  };

  const handleGatingFactorChange = (factor, value) => {
    setGatingFactors((prev) => ({
      ...prev,
      [factor]: parseFloat(value) || 0,
    }));
  };

  const handleApply = async () => {
    try {
      // Update ring prompts and gating factors
      await Promise.all([
        ...rings.map((ring) => apiClient.updateRing(ring.ringId, ring)),
        apiClient.updateGatingFactors(gatingFactors),
      ]);
      
      // Trigger AI categorization of all devices based on updated prompts
      setLoading(true);
      await apiClient.aiCategorizeDevices();
      
      alert('Configurations updated and devices recategorized successfully!');
    } catch (error) {
      console.error('Error updating configurations:', error);
      alert('Failed to update configurations: ' + error.message);
    } finally {
      setLoading(false);
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
          Rings
        </Typography>
        <Button
          variant="contained"
          color="primary"
          size="large"
          onClick={handleApply}
        >
          Apply
        </Button>
      </Box>

      {/* Default Gating Factors Section */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Default Gating Factors
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          These gating factors will be applied to all new deployments.
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={4}>
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Avg CPU Usage Max (%)
              </Typography>
              <TextField
                fullWidth
                type="number"
                value={gatingFactors.avgCpuUsageMax || ''}
                onChange={(e) => handleGatingFactorChange('avgCpuUsageMax', e.target.value)}
                placeholder="100"
                inputProps={{ min: 0, max: 100 }}
              />
            </Paper>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Avg Memory Usage Max (%)
              </Typography>
              <TextField
                fullWidth
                type="number"
                value={gatingFactors.avgMemoryUsageMax || ''}
                onChange={(e) => handleGatingFactorChange('avgMemoryUsageMax', e.target.value)}
                placeholder="100"
                inputProps={{ min: 0, max: 100 }}
              />
            </Paper>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Avg Disk Free Space Min (%)
              </Typography>
              <TextField
                fullWidth
                type="number"
                value={gatingFactors.avgDiskFreeSpaceMin || ''}
                onChange={(e) => handleGatingFactorChange('avgDiskFreeSpaceMin', e.target.value)}
                placeholder="--"
                inputProps={{ min: 0, max: 100 }}
              />
            </Paper>
          </Grid>
        </Grid>
      </Paper>

      {/* Ring Configuration Section */}
      <Typography variant="h6" gutterBottom>
        Ring Configurations
      </Typography>
      {rings.map((ring) => (
        <Accordion key={ring.ringId} elevation={2} sx={{ mb: 2 }} defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6">{ring.ringName}</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                Categorization Prompt
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Describe the criteria for devices to be assigned to this ring. AI will evaluate each device's data against this prompt. Higher ring numbers have priority.
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={3}
                value={ring.categorizationPrompt}
                onChange={(e) => handlePromptChange(ring.ringId, e.target.value)}
                placeholder="e.g., 'VIP devices with critical business functions and high uptime requirements'"
              />
            </Box>
          </AccordionDetails>
        </Accordion>
      ))}
    </Box>
  );
}
