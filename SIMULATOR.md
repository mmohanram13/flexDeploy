# Simulator Module

The FlexDeploy Simulator provides a comprehensive UI and API for testing deployment scenarios without affecting real devices.

## Overview

The simulator is architecturally modular with components separated into:
- **Server Service** (`server/simulator_service.py`) - Business logic for simulation operations
- **API Endpoints** (`server/main.py`) - REST endpoints for simulator operations
- **UI Interface** (`ui/src/pages/Simulator.jsx`) - Web interface for controlling simulations

## Accessing the Simulator

### Web UI
Navigate to: **http://localhost:5173/simulator**

### API Base URL
```
http://localhost:8000/api/simulator
```

## Features

### 1. Stress Profiles
Pre-configured stress levels that can be applied to all devices in a ring:

| Level | CPU | Memory | Disk | Use Case |
|-------|-----|--------|------|----------|
| **Low** | 25% | 30% | 20% | Healthy baseline |
| **Normal** | 50% | 55% | 45% | Typical operation |
| **High** | 75% | 80% | 70% | Heavy load testing |
| **Critical** | 95% | 92% | 88% | Failure scenarios |

### 2. Custom Metrics
Set specific CPU, Memory, and Disk usage values for all devices in a selected ring.

### 3. Deployment Status Control
Manually update the deployment status of any ring:
- Not Started
- Started
- In Progress
- Completed
- Failed
- Stopped

### 4. Real-time Device View
View all devices in the selected ring with their current metrics and risk scores.

## API Endpoints

### POST /api/simulator/devices
Create or update a device.

**Request:**
```json
{
  "deviceId": "DEV-001",
  "deviceName": "Test Device",
  "manufacturer": "Dell",
  "model": "Latitude",
  "osName": "Windows 10",
  "site": "HQ",
  "department": "IT",
  "ring": 0,
  "totalMemory": "16GB",
  "totalStorage": "512GB",
  "networkSpeed": "1Gbps",
  "avgCpuUsage": 75.0,
  "avgMemoryUsage": 80.0,
  "avgDiskSpace": 60.0,
  "riskScore": 50
}
```

**Response:**
```json
{
  "status": "success",
  "deviceId": "DEV-001",
  "riskScore": 45
}
```

### POST /api/simulator/device-metrics
Update metrics for a specific device.

**Request:**
```json
{
  "deviceId": "DEV-001",
  "avgCpuUsage": 85.0,
  "avgMemoryUsage": 90.0,
  "avgDiskSpace": 70.0
}
```

### POST /api/simulator/ring-metrics
Update metrics for all devices in a ring.

**Request:**
```json
{
  "deploymentId": "DEP-001",
  "ringId": 0,
  "avgCpuUsage": 75.0,
  "avgMemoryUsage": 80.0,
  "avgDiskSpace": 70.0
}
```

**Response:**
```json
{
  "status": "success",
  "ringId": 0,
  "devicesUpdated": 5
}
```

### POST /api/simulator/deployment-status
Update deployment ring status.

**Request:**
```json
{
  "deploymentId": "DEP-001",
  "ringId": 0,
  "status": "In Progress",
  "failureReason": "Optional failure message"
}
```

### GET /api/simulator/deployment/{deployment_id}/ring/{ring_id}/devices
Get all devices in a ring.

**Response:**
```json
{
  "deploymentId": "DEP-001",
  "ringId": 0,
  "devices": [
    {
      "deviceId": "DEV-001",
      "deviceName": "Device 1",
      "avgCpuUsage": 75.0,
      "avgMemoryUsage": 80.0,
      "avgDiskSpace": 60.0,
      "riskScore": 45
    }
  ]
}
```

### POST /api/simulator/stress-profile
Apply a pre-configured stress profile.

**Request:**
```json
{
  "deploymentId": "DEP-001",
  "ringId": 0,
  "stressLevel": "high"
}
```

**Response:**
```json
{
  "status": "success",
  "ringId": 0,
  "stressLevel": "high",
  "devicesUpdated": 5,
  "profile": {
    "cpu": 75.0,
    "memory": 80.0,
    "disk": 70.0
  }
}
```

## Using the Web UI

### Step 1: Select Deployment and Ring
1. Open http://localhost:5173/simulator
2. Select a deployment from the dropdown
3. Select a ring (0-3)

### Step 2: Apply Stress Profile
1. Choose a stress level (Low, Normal, High, Critical)
2. Review the profile metrics displayed
3. Click "Apply Stress Profile"
4. View updated devices in the table below

### Step 3: Apply Custom Metrics
1. Enter specific values for CPU, Memory, and/or Disk usage
2. Leave fields empty to keep current values
3. Click "Apply Custom Metrics"
4. Devices will update with new metrics

### Step 4: Control Deployment Status
1. Click any status button to update the ring's deployment status
2. Status changes are immediately reflected in the deployment detail page

## Risk Score Calculation

Risk scores are automatically calculated based on resource usage:

```
avg_usage = (CPU + Memory + (100 - Disk)) / 3

If avg_usage > 80%:
  risk_score = 0-30 (High Risk - Red)
Else if avg_usage > 50%:
  risk_score = 31-70 (Medium Risk - Yellow)
Else:
  risk_score = 71-100 (Low Risk - Green)
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│              Simulator UI                        │
│        (ui/src/pages/Simulator.jsx)             │
└────────────────┬────────────────────────────────┘
                 │
                 │ HTTP REST API
                 ▼
┌─────────────────────────────────────────────────┐
│          API Endpoints                           │
│         (server/main.py)                         │
│                                                  │
│  - POST /api/simulator/devices                   │
│  - POST /api/simulator/device-metrics            │
│  - POST /api/simulator/ring-metrics              │
│  - POST /api/simulator/deployment-status         │
│  - POST /api/simulator/stress-profile            │
│  - GET  /api/simulator/.../devices               │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│        Simulator Service                         │
│    (server/simulator_service.py)                 │
│                                                  │
│  Business Logic:                                 │
│  - create_or_update_device()                     │
│  - update_device_metrics()                       │
│  - update_ring_metrics()                         │
│  - update_deployment_ring_status()               │
│  - get_ring_devices()                            │
│  - apply_stress_profile()                        │
│  - _calculate_risk_score()                       │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│           SQLite Database                        │
│          (flexdeploy.db)                         │
│                                                  │
│  Tables:                                         │
│  - devices                                       │
│  - deployment_rings                              │
│  - deployments                                   │
└─────────────────────────────────────────────────┘
```

## Example Usage Scenarios

### Scenario 1: Test Successful Deployment
1. Navigate to Simulator page
2. Select "DEP-001" and "Ring 0"
3. Apply "Low" stress profile
4. Set status to "Completed"
5. Repeat for remaining rings

### Scenario 2: Simulate Deployment Failure
1. Select "DEP-001" and "Ring 1"
2. Apply "Critical" stress profile
3. Set status to "Failed"
4. View failure analysis in deployment details

### Scenario 3: Gradual Load Increase
1. Select "DEP-001" and "Ring 2"
2. Start with "Low" stress profile
3. Progressively apply Normal → High → Critical
4. Monitor risk scores in device table

### Scenario 4: Custom Metric Testing
1. Enter specific values: CPU: 85%, Memory: 90%, Disk: 75%
2. Apply to test specific threshold scenarios
3. Verify gating factor behavior

## Benefits

- **No Production Impact** - Test freely without affecting real systems
- **Rapid Iteration** - Instantly apply different scenarios
- **Visual Feedback** - See results immediately in the UI
- **Comprehensive Control** - Manage metrics and status independently
- **Modular Design** - Service layer separates business logic from endpoints
- **Reusable** - API can be called from scripts or other tools

## Tips

- Use the simulator in conjunction with the deployment detail page for full visibility
- Apply stress profiles first, then fine-tune with custom metrics
- Watch the devices table to see risk scores update in real-time
- Test gating factor logic by setting specific metric combinations
- Use status controls to simulate deployment progression or failures
