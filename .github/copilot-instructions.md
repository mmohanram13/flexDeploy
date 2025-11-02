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

Ring Categorization Logic:
- Each device's data is evaluated against ring prompts using AI
- Rings are evaluated in priority order from highest (Ring 3) to lowest (Ring 0)
- Device is assigned to the FIRST ring whose criteria it matches
- Higher ring numbers have priority over lower ones
- Categorization happens on initial setup and when "Apply" button is clicked on Rings page

Deployment Gating Logic:
- Gating prompts determine whether to proceed from one ring to the next during deployment
- AI analyzes device metrics from current ring against the gating prompt
- Decision is made whether deployment can proceed to next ring or should stop

General:

1. Never add icon before any text unless specified.
2. The UI code is under ui/ folder, server code under server/ folder, and the simulator covers the simulator/ folder.
3. For python packages, use uv for package versions.


To run the UI and backend server, always set python virtual environment and then run:

```bash
./run_app.sh
```

You will servers running as below in port 8000 for server and 5173 for UI.
Services:
  ✓ Backend:  http://localhost:8000
  ✓ Frontend: http://localhost:5173
  ✓ API Docs: http://localhost:8000/docs

Logs:
  Server: tail -f server.log
  UI:     tail -f ui.log