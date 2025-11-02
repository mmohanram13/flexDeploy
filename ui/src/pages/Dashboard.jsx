import React from 'react';
import { Box, Card, CardContent, Typography, Grid, Paper } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { dashboardMetrics, deviceDistributionByRing } from '../data/mockData';

export default function Dashboard() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', alignItems: 'stretch' }}>
        {/* Left Half - Metric Cards Stacked */}
        <Box sx={{ flex: '0 0 calc(50% - 12px)', display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Card elevation={2} sx={{ flex: 1 }}>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Devices
              </Typography>
              <Typography variant="h3" component="div">
                {dashboardMetrics.totalDevices}
              </Typography>
            </CardContent>
          </Card>
          
          <Card elevation={2} sx={{ flex: 1 }}>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Deployments
              </Typography>
              <Typography variant="h3" component="div" color="primary">
                {dashboardMetrics.totalDeployments}
              </Typography>
            </CardContent>
          </Card>
          
          <Card elevation={2} sx={{ flex: 1 }}>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Active Rings
              </Typography>
              <Typography variant="h3" component="div" color="secondary">
                {dashboardMetrics.activeRings}
              </Typography>
            </CardContent>
          </Card>
        </Box>

        {/* Right Half - Chart Full Width */}
        <Box sx={{ flex: '0 0 calc(50% - 12px)' }}>
          <Paper elevation={2} sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
            <Typography variant="h6" gutterBottom>
              Number of Devices per Ring
            </Typography>
            <Box sx={{ flex: 1, minHeight: 0 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={deviceDistributionByRing}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="value" fill="#2196f3" name="Devices" />
                </BarChart>
              </ResponsiveContainer>
            </Box>
          </Paper>
        </Box>
      </Box>
    </Box>
  );
}
