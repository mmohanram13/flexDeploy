import React, { useState } from 'react';
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
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { rings as initialRings } from '../data/mockData';

export default function Rings() {
  const [rings, setRings] = useState(initialRings);

  const handlePromptChange = (ringId, value) => {
    setRings((prevRings) =>
      prevRings.map((ring) =>
        ring.ringId === ringId ? { ...ring, categorizationPrompt: value } : ring
      )
    );
  };

  const handleGatingFactorChange = (ringId, factor, value) => {
    setRings((prevRings) =>
      prevRings.map((ring) =>
        ring.ringId === ringId
          ? {
              ...ring,
              gatingFactors: {
                ...ring.gatingFactors,
                [factor]: value,
              },
            }
          : ring
      )
    );
  };

  const handleApply = () => {
    // TODO: Implement ring recategorization logic based on prompts and gating factors
    console.log('Applying ring categorization with:', rings);
  };

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
                      value={ring.gatingFactors.avgCPUUsageMax}
                      onChange={(e) =>
                        handleGatingFactorChange(ring.ringId, 'avgCPUUsageMax', e.target.value)
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
                      value={ring.gatingFactors.avgMemoryUsageMax}
                      onChange={(e) =>
                        handleGatingFactorChange(ring.ringId, 'avgMemoryUsageMax', e.target.value)
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
                      value={ring.gatingFactors.avgDiskFreeSpaceMin}
                      onChange={(e) =>
                        handleGatingFactorChange(ring.ringId, 'avgDiskFreeSpaceMin', e.target.value)
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
