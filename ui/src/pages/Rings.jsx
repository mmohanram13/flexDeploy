import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Card,
  CardContent,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  RadioGroup,
  FormControlLabel,
  Radio,
  Grid,
  Chip,
  Divider,
} from '@mui/material';
import { rings as ringsData } from '../data/mockData';

export default function Rings() {
  const [rings, setRings] = useState(ringsData);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedRing, setSelectedRing] = useState(null);

  const handleEditRing = (ring) => {
    setSelectedRing({ ...ring });
    setEditDialogOpen(true);
  };

  const handleSaveRing = () => {
    // Update the ring in the array
    setRings(rings.map(r => r.id === selectedRing.id ? selectedRing : r));
    setEditDialogOpen(false);
    setSelectedRing(null);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Ring Configuration</Typography>
        <Button variant="contained" startIcon={<span>+</span>}>
          Add Ring
        </Button>
      </Box>

      {rings.map((ring) => (
        <Card key={ring.id} elevation={2} sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Chip
                  label={`Ring ${ring.id}`}
                  sx={{
                    bgcolor: ring.color,
                    color: 'white',
                    fontWeight: 600,
                  }}
                />
                <Typography variant="h6">{ring.displayName}</Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button size="small" variant="outlined" onClick={() => handleEditRing(ring)}>
                  Edit
                </Button>
                <Button size="small" variant="outlined" color="error">
                  Delete
                </Button>
              </Box>
            </Box>

            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              <strong>Description for AI Categorization:</strong>
            </Typography>
            <Typography variant="body2" sx={{ mb: 2, fontStyle: 'italic', bgcolor: 'grey.50', p: 1.5, borderRadius: 1 }}>
              "{ring.description}"
            </Typography>

            <Divider sx={{ my: 2 }} />

            <Typography variant="body2" fontWeight={600} gutterBottom>
              Monitoring Configuration:
            </Typography>
            <Box sx={{ pl: 2, mb: 2 }}>
              <Typography variant="body2">
                • Monitor Duration: {ring.monitoring.duration} {ring.monitoring.durationUnit}
              </Typography>
              <Typography variant="body2">
                • Wait Before Next Ring: {ring.monitoring.waitBeforeNext} {ring.monitoring.waitUnit}
              </Typography>
            </Box>

            <Typography variant="body2" fontWeight={600} gutterBottom>
              Gating Thresholds:
            </Typography>
            <Box sx={{ pl: 2, mb: 2 }}>
              <Typography variant="body2">
                • Success Threshold to Proceed: {ring.thresholds.successRate}%
              </Typography>
              <Typography variant="body2">
                • Max Anomaly Rate: {ring.thresholds.maxAnomalyRate}%
              </Typography>
              <Typography variant="body2">
                • CPU Deviation Threshold: {ring.thresholds.cpuDeviation}%
              </Typography>
              <Typography variant="body2">
                • Memory Spike Threshold: {ring.thresholds.memorySpike}%
              </Typography>
            </Box>

            <Typography variant="body2" fontWeight={600} gutterBottom>
              Gating Rules:
            </Typography>
            <Box sx={{ pl: 2, mb: 2 }}>
              <Typography variant="body2">
                • If anomalies &gt; threshold:{' '}
                <Chip
                  label={ring.gating.onAnomalies.toUpperCase()}
                  size="small"
                  color={ring.gating.onAnomalies === 'stop' ? 'error' : 'warning'}
                />
              </Typography>
              <Typography variant="body2" sx={{ mt: 0.5 }}>
                • If success &lt; threshold:{' '}
                <Chip
                  label={ring.gating.onFailure.toUpperCase()}
                  size="small"
                  color={ring.gating.onFailure === 'stop' ? 'error' : 'warning'}
                />
              </Typography>
            </Box>

            {ring.metricsMonitored && (
              <>
                <Typography variant="body2" fontWeight={600} gutterBottom>
                  AI Metrics Monitored:
                </Typography>
                <Box sx={{ pl: 2 }}>
                  {ring.metricsMonitored.map((metric, idx) => (
                    <Typography key={idx} variant="body2">
                      • {metric}
                    </Typography>
                  ))}
                </Box>
              </>
            )}

            <Divider sx={{ my: 2 }} />

            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="body2" fontWeight={600}>
                Current Devices: {ring.deviceCount}
              </Typography>
              <Button size="small" variant="text">
                View Devices
              </Button>
            </Box>
          </CardContent>
        </Card>
      ))}

      {/* Edit Ring Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="md" fullWidth>
        {selectedRing && (
          <>
            <DialogTitle>Edit Ring: {selectedRing.displayName}</DialogTitle>
            <DialogContent>
              <TextField
                fullWidth
                label="Ring Name"
                value={selectedRing.name}
                onChange={(e) => setSelectedRing({ ...selectedRing, name: e.target.value })}
                sx={{ mt: 2, mb: 2 }}
              />

              <Typography variant="body2" gutterBottom>
                Description (AI uses this to categorize devices):
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={3}
                value={selectedRing.description}
                onChange={(e) => setSelectedRing({ ...selectedRing, description: e.target.value })}
                sx={{ mb: 3 }}
              />

              <Paper sx={{ p: 2, mb: 3, bgcolor: 'grey.50' }}>
                <Typography variant="h6" gutterBottom>
                  Monitoring Configuration
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Monitor Duration"
                      value={selectedRing.monitoring.duration}
                      onChange={(e) =>
                        setSelectedRing({
                          ...selectedRing,
                          monitoring: { ...selectedRing.monitoring, duration: parseInt(e.target.value) },
                        })
                      }
                      helperText="How long to monitor this ring before proceeding"
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      select
                      fullWidth
                      label="Unit"
                      value={selectedRing.monitoring.durationUnit}
                      onChange={(e) =>
                        setSelectedRing({
                          ...selectedRing,
                          monitoring: { ...selectedRing.monitoring, durationUnit: e.target.value },
                        })
                      }
                    >
                      <MenuItem value="minutes">Minutes</MenuItem>
                      <MenuItem value="hours">Hours</MenuItem>
                    </TextField>
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Wait Before Next Ring"
                      value={selectedRing.monitoring.waitBeforeNext}
                      onChange={(e) =>
                        setSelectedRing({
                          ...selectedRing,
                          monitoring: { ...selectedRing.monitoring, waitBeforeNext: parseInt(e.target.value) },
                        })
                      }
                      helperText="Delay after monitoring ends"
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      select
                      fullWidth
                      label="Unit"
                      value={selectedRing.monitoring.waitUnit}
                      onChange={(e) =>
                        setSelectedRing({
                          ...selectedRing,
                          monitoring: { ...selectedRing.monitoring, waitUnit: e.target.value },
                        })
                      }
                    >
                      <MenuItem value="minutes">Minutes</MenuItem>
                      <MenuItem value="hours">Hours</MenuItem>
                    </TextField>
                  </Grid>
                </Grid>
              </Paper>

              <Paper sx={{ p: 2, mb: 3, bgcolor: 'grey.50' }}>
                <Typography variant="h6" gutterBottom>
                  Gating Thresholds (AI uses these to decide)
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Success Threshold (%)"
                      value={selectedRing.thresholds.successRate}
                      onChange={(e) =>
                        setSelectedRing({
                          ...selectedRing,
                          thresholds: { ...selectedRing.thresholds, successRate: parseInt(e.target.value) },
                        })
                      }
                      helperText="Min % of successful deployments to proceed"
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Max Anomaly Rate (%)"
                      value={selectedRing.thresholds.maxAnomalyRate}
                      onChange={(e) =>
                        setSelectedRing({
                          ...selectedRing,
                          thresholds: { ...selectedRing.thresholds, maxAnomalyRate: parseInt(e.target.value) },
                        })
                      }
                      helperText="Max % of devices with anomalies before pausing"
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="CPU Deviation Threshold (%)"
                      value={selectedRing.thresholds.cpuDeviation}
                      onChange={(e) =>
                        setSelectedRing({
                          ...selectedRing,
                          thresholds: { ...selectedRing.thresholds, cpuDeviation: parseInt(e.target.value) },
                        })
                      }
                      helperText="% change from baseline to flag anomaly"
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Memory Spike Threshold (%)"
                      value={selectedRing.thresholds.memorySpike}
                      onChange={(e) =>
                        setSelectedRing({
                          ...selectedRing,
                          thresholds: { ...selectedRing.thresholds, memorySpike: parseInt(e.target.value) },
                        })
                      }
                      helperText="% spike to flag anomaly"
                    />
                  </Grid>
                </Grid>
              </Paper>

              <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                <Typography variant="h6" gutterBottom>
                  Gating Actions (What AI should do)
                </Typography>
                <Typography variant="body2" gutterBottom>
                  If anomalies &gt; threshold:
                </Typography>
                <RadioGroup
                  row
                  value={selectedRing.gating.onAnomalies}
                  onChange={(e) =>
                    setSelectedRing({
                      ...selectedRing,
                      gating: { ...selectedRing.gating, onAnomalies: e.target.value },
                    })
                  }
                  sx={{ mb: 2 }}
                >
                  <FormControlLabel value="continue" control={<Radio />} label="Continue" />
                  <FormControlLabel value="pause" control={<Radio />} label="Pause" />
                  <FormControlLabel value="stop" control={<Radio />} label="Stop" />
                </RadioGroup>

                <Typography variant="body2" gutterBottom>
                  If success &lt; threshold:
                </Typography>
                <RadioGroup
                  row
                  value={selectedRing.gating.onFailure}
                  onChange={(e) =>
                    setSelectedRing({
                      ...selectedRing,
                      gating: { ...selectedRing.gating, onFailure: e.target.value },
                    })
                  }
                >
                  <FormControlLabel value="continue" control={<Radio />} label="Continue" />
                  <FormControlLabel value="pause" control={<Radio />} label="Pause" />
                  <FormControlLabel value="stop" control={<Radio />} label="Stop" />
                </RadioGroup>
              </Paper>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
              <Button variant="contained" onClick={handleSaveRing}>
                Save Ring Configuration
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
}
