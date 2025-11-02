// Mock data for FlexDeploy - AI Deployment Orchestrator
// NOTE: All data is now managed by the backend and populated via the simulator
// This file is kept for backward compatibility but should not be used for seeding data
// 
// Data source: server/init_data.py (centralized initialization)

export const devices = [];
export const deployments = [];
export const deploymentDetails = {};

// Ring data is now fetched from the backend API
// Do not use this for initialization - use server/init_data.py instead
export const rings = [];

// Dashboard data is fetched from backend
export const dashboardMetrics = {
  totalDevices: 0,
  totalDeployments: 0,
  activeRings: 0,
};

export const deviceDistributionByRing = [
  { name: 'Ring 0', value: 0 },
  { name: 'Ring 1', value: 0 },
  { name: 'Ring 2', value: 0 },
  { name: 'Ring 3', value: 0 },
];

