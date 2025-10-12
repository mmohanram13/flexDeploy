import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Paper,
  List,
  ListItem,
  ListItemText,
  Button,
  Chip,
} from '@mui/material';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { dashboardMetrics, aiActivities, deviceDistribution } from '../data/mockData';

export default function Dashboard() {
  const navigate = useNavigate();

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      {/* Metrics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={4}>
          <Card elevation={2}>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total Devices
              </Typography>
              <Typography variant="h3" component="div">
                {dashboardMetrics.totalDevices}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card elevation={2}>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Active Deployments
              </Typography>
              <Typography variant="h3" component="div" color="primary">
                {dashboardMetrics.activeDeployments}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card elevation={2}>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                AI Cohorts Generated
              </Typography>
              <Typography variant="h3" component="div" color="secondary">
                {dashboardMetrics.aiCohortsGenerated}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent AI Activity */}
      <Paper elevation={2} sx={{ mb: 4, p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Recent AI Activity
        </Typography>
        <List>
          {aiActivities.map((activity, index) => (
            <React.Fragment key={activity.id}>
              <ListItem
                sx={{
                  bgcolor: 'background.default',
                  borderRadius: 1,
                  mb: 1,
                }}
              >
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body1" component="span">
                        {activity.icon}
                      </Typography>
                      <Typography variant="body1" component="span" fontWeight={600}>
                        {activity.title}
                      </Typography>
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {activity.description}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {activity.timestamp}
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>
            </React.Fragment>
          ))}
        </List>
      </Paper>

      {/* Device Distribution by Ring */}
      <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Device Distribution by Ring
        </Typography>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={deviceDistribution}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              fill="#8884d8"
              paddingAngle={2}
              dataKey="value"
              label={(entry) => `${entry.name}: ${entry.value}`}
            >
              {deviceDistribution.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </Paper>

      {/* Create Deployment Button */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
        <Button
          variant="contained"
          size="large"
          startIcon={<span>+</span>}
          onClick={() => navigate('/deployments')}
        >
          Create Deployment
        </Button>
      </Box>
    </Box>
  );
}
