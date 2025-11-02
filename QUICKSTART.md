# FlexDeploy - Quick Start Guide

## 🚀 Start the Application

### Step 1: Start the API Server
```bash
cd /Users/mohan-10180/Documents/project-l/flexDeploy
uv run uvicorn server.main:app --host 0.0.0.0 --port 8000
```
API will be available at: **http://localhost:8000**

### Step 2: Start the UI
```bash
cd /Users/mohan-10180/Documents/project-l/flexDeploy/ui
npm run dev
```
UI will be available at: **http://localhost:5173** (or 5174 if 5173 is in use)

## ✅ What's Running

- **Backend API**: http://localhost:8000
  - REST API endpoints
  - SQLite database (server/flexdeploy.db)
  - API docs: http://localhost:8000/docs

- **Frontend UI**: http://localhost:5173
  - React application with Material-UI
  - Real-time data from API

## 📊 Current Data

- **15 Devices** across 4 rings
- **4 Deployments** with various statuses
- **4 Rings** (Canary, Low Risk, High Risk, VIP)

## 🔧 Common Tasks

### Reset Database
```bash
uv run python -m server.migrate_data
```

### Test API
```bash
# Get dashboard metrics
curl http://localhost:8000/api/dashboard/metrics

# Get all devices
curl http://localhost:8000/api/devices
```

### View Database
```bash
sqlite3 server/flexdeploy.db
.tables
SELECT * FROM devices LIMIT 5;
```

## 📚 Full Documentation

See **DATABASE_MIGRATION.md** for complete documentation on:
- Database schema
- API endpoints
- Migration details
- Troubleshooting

## ✨ Features

- ✅ Complete SQLite database
- ✅ REST API with FastAPI
- ✅ React UI with Material-UI
- ✅ Real-time data loading
- ✅ CRUD operations for rings
- ✅ Deployment management
- ✅ Device monitoring
