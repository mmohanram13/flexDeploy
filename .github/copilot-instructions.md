Architecture:

Design Language - Material UI

Left - Pane:
- Dashboard
- Devices
- Deployments
- Rings

Dashboard:

Section 1: (Left Side)

3 cards auto adjusted vertically:
- Total Devices
- Total Deployments
- Active Rings

Section 2: (Right Side)

Graph showing number of devices per ring

Devices:

Table with columns scrollable horizontally if needed:

- Device ID
- Device Name
- Manufacturer
- Model
- OS Name
- Site
- Department
- Ring
- Total Memory
- Total Storage
- Network Speed
- Average CPU Usage
- Average Memory Usage
- Average Disk Space
- Risk Score (>80% Avg CPU/Memory/Disk Usage - Score 0-30, >50% - Score 31-70, <=50% - Score 71-100 using linear interpolation)

Deployments:

4 Demo Deployments listed in a table with columns:
- Deployment ID
- Deployment Name
- Run (Status needs to be tracked - Not Started, In Progress, Completed, Failed, Stopped)
- View Details

View Details page:
- Deployment ID
- Deployment Name

Accordion for each Ring:
  - Ring Name
  - Number of Devices
  - Status (Not Started, In Progress, Completed, Failed, Stopped)
  - If failed, need reason why failed

Rings:

Ring 0 - Canary (Test Bed)
Ring 1 - Low Risk Devices
Ring 2 - High Risk Devices
Ring 3 - VIP Devices

For each ring, there should be a prompt field to record how to categorize devices into this ring.
Another input field to know the gating factors (risk score, average cpu usage, average memory usage, average disk free space) for this ring.

General:

1. Never add icon before any text unless specified.
2. The UI code is under ui/ folder, server code under server/ folder, and the simulator covers the simulator/ folder.
3. For python packages, use uv for package versions.
