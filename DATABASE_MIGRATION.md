# Database Migration - SQLite Implementation

## Overview

The FlexDeploy application has been successfully migrated from using mock data (JavaScript files) to a SQLite database. All data is now persisted and accessed through a FastAPI REST API.

## Database Schema

### Tables

1. **devices** - Stores device information
   - device_id (TEXT, PRIMARY KEY)
   - device_name, manufacturer, model, os_name
   - site, department, ring
   - total_memory, total_storage, network_speed
   - avg_cpu_usage, avg_memory_usage, avg_disk_space
   - risk_score
   - timestamps (created_at, updated_at)

2. **deployments** - Stores deployment records
   - deployment_id (TEXT, PRIMARY KEY)
   - deployment_name
   - status (Not Started, In Progress, Completed, Failed, Stopped)
   - timestamps (created_at, updated_at)

3. **deployment_rings** - Tracks ring status per deployment
   - id (INTEGER, PRIMARY KEY, AUTOINCREMENT)
   - deployment_id, ring_id (FOREIGN KEYS)
   - ring_name, device_count, status
   - failure_reason (nullable)
   - timestamps (created_at, updated_at)

4. **rings** - Ring configuration
   - ring_id (INTEGER, PRIMARY KEY)
   - ring_name, categorization_prompt
   - Gating factors: risk_score_min/max, avg_cpu_usage_max, avg_memory_usage_max, avg_disk_free_space_min
   - timestamps (created_at, updated_at)

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌──────────────┐
│   UI (React)│ ◄─HTTP──┤ FastAPI REST │ ◄─SQL───┤    SQLite    │
│  (Port 5173)│         │  (Port 8000) │         │   Database   │
└─────────────┘         └──────────────┘         └──────────────┘
```

## Files Created/Modified

### Server Files
- `server/database.py` - Database schema and initialization
- `server/migrate_data.py` - Data migration script
- `server/main.py` - FastAPI server with REST endpoints
- `server/__init__.py` - Python module initialization
- `server/flexdeploy.db` - SQLite database file

### UI Files
- `ui/src/api/client.js` - API client for backend communication
- `ui/src/pages/Dashboard.jsx` - Updated to use API
- `ui/src/pages/Devices.jsx` - Updated to use API
- `ui/src/pages/Deployments.jsx` - Updated to use API
- `ui/src/pages/DeploymentDetail.jsx` - Updated to use API
- `ui/src/pages/Rings.jsx` - Updated to use API

## Setup Instructions

### 1. Install Dependencies

```bash
# Install Python dependencies
cd /path/to/flexDeploy
uv sync

# Install Node dependencies (if not already done)
cd ui
npm install
```

### 2. Initialize Database

```bash
# Run migration script to create and populate database
cd /path/to/flexDeploy
uv run python -m server.migrate_data
```

This will:
- Create all database tables
- Populate with initial data (15 devices, 4 rings, 4 deployments)
- Display migration summary

### 3. Start the API Server

```bash
cd /path/to/flexDeploy
uv run uvicorn server.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

API Documentation (Swagger): `http://localhost:8000/docs`

### 4. Start the UI

```bash
cd /path/to/flexDeploy
npm run dev --prefix ui
```

The UI will be available at `http://localhost:5173`

## API Endpoints

### Dashboard
- `GET /api/dashboard/metrics` - Get dashboard metrics (device/deployment/ring counts)
- `GET /api/dashboard/device-distribution` - Get device count per ring

### Devices
- `GET /api/devices` - Get all devices

### Deployments
- `GET /api/deployments` - Get all deployments
- `GET /api/deployments/{deployment_id}` - Get deployment details with ring status
- `POST /api/deployments/{deployment_id}/run` - Start a deployment
- `POST /api/deployments/{deployment_id}/stop` - Stop a deployment

### Rings
- `GET /api/rings` - Get all ring configurations
- `PUT /api/rings/{ring_id}` - Update ring configuration

## Testing

Test the API endpoints:

```bash
# Dashboard metrics
curl http://localhost:8000/api/dashboard/metrics

# List all devices
curl http://localhost:8000/api/devices

# List all deployments
curl http://localhost:8000/api/deployments

# List all rings
curl http://localhost:8000/api/rings
```

Or run the test script:
```bash
./test_api.sh
```

## Database Management

### Reset Database

To reset the database and start fresh:

```bash
uv run python -m server.migrate_data
```

This will drop all tables and recreate them with the initial data.

### Backup Database

```bash
cp server/flexdeploy.db server/flexdeploy.db.backup
```

### Query Database Directly

```bash
sqlite3 server/flexdeploy.db
```

Example queries:
```sql
-- View all devices
SELECT * FROM devices;

-- View deployment status
SELECT d.deployment_name, d.status, COUNT(dr.id) as ring_count
FROM deployments d
LEFT JOIN deployment_rings dr ON d.deployment_id = dr.deployment_id
GROUP BY d.deployment_id;

-- View device distribution by ring
SELECT ring, COUNT(*) as count FROM devices GROUP BY ring;
```

## Migration Summary

✅ **Completed:**
- Database schema designed and implemented
- Mock data migrated to SQLite (15 devices, 4 deployments, 4 rings)
- REST API created with FastAPI
- All UI pages updated to fetch data from API
- Loading states added to UI
- CORS configured for local development

**Data Migrated:**
- 15 Devices
- 4 Rings (0: Canary, 1: Low Risk, 2: High Risk, 3: VIP)
- 4 Deployments
- 16 Deployment Ring Status Records

## Next Steps

Consider these enhancements:
1. Add database indexes for performance
2. Implement authentication/authorization
3. Add data validation and error handling
4. Create database migration system (e.g., Alembic)
5. Add logging and monitoring
6. Implement real-time updates (WebSockets)
7. Add unit and integration tests
8. Deploy to production environment
