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

  useEffect(() => {
    fetchRings();
  }, []);

  const fetchRings = async () => {
    try {
      const data = await apiClient.getRings();
      setRings(data);
    } catch (error) {
      console.error('Error fetching rings:', error);
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

  const handleGatingFactorChange = (ringId, factorPath, value) => {
    setRings((prevRings) =>
      prevRings.map((ring) => {
        if (ring.ringId !== ringId) return ring;
        
        const newGatingFactors = { ...ring.gatingFactors };
        const [factor, subkey] = factorPath.split('.');
        
        if (subkey) {
          newGatingFactors[factor] = {
            ...newGatingFactors[factor],
            [subkey]: parseFloat(value) || 0,
          };
        } else {
          newGatingFactors[factor] = parseFloat(value) || 0;
        }
        
        return {
          ...ring,
          gatingFactors: newGatingFactors,
        };
      })
    );
  };

  const handleApply = async () => {
    try {
      await Promise.all(
        rings.map((ring) => apiClient.updateRing(ring.ringId, ring))
      );
      alert('Ring configurations updated successfully!');
    } catch (error) {
      console.error('Error updating rings:', error);
      alert('Failed to update ring configurations');
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
              <TextField
                fullWidth
                multiline
                rows={3}
                value={ring.categorizationPrompt}
                onChange={(e) => handlePromptChange(ring.ringId, e.target.value)}
                placeholder="Describe how devices should be categorized into this ring..."
                sx={{ mb: 3 }}
              />

              <Typography variant="subtitle1" gutterBottom>
                Gating Factors
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
                      value={ring.gatingFactors.avgCpuUsage?.max || ''}
                      onChange={(e) =>
                        handleGatingFactorChange(ring.ringId, 'avgCpuUsage.max', e.target.value)
                      }
                      placeholder="--"
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
                      value={ring.gatingFactors.avgMemoryUsage?.max || ''}
                      onChange={(e) =>
                        handleGatingFactorChange(ring.ringId, 'avgMemoryUsage.max', e.target.value)
                      }
                      placeholder="--"
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
                      value={ring.gatingFactors.avgDiskFreeSpace?.min || ''}
                      onChange={(e) =>
                        handleGatingFactorChange(ring.ringId, 'avgDiskFreeSpace.min', e.target.value)
                      }
                      placeholder="--"
                      inputProps={{ min: 0, max: 100 }}
                    />
                  </Paper>
                </Grid>
              </Grid>
            </Box>
          </AccordionDetails>
        </Accordion>
      ))}
    </Box>
  );
}
