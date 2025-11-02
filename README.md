# FlexDeploy - AI-Powered Deployment Orchestrator

> Make your deployments reliable with AI-driven ring-based deployment strategies powered by AWS Bedrock and Amazon Nova models.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node](https://img.shields.io/badge/Node-18+-green.svg)](https://nodejs.org/)
[![React](https://img.shields.io/badge/React-19+-61DAFB.svg)](https://reactjs.org/)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock-orange.svg)](https://aws.amazon.com/bedrock/)

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [AI Agents](#ai-agents)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Security](#security)

> 💡 **Quick Reference**: See [COMMANDS.md](COMMANDS.md) for common commands and quick fixes.

## 🎯 Overview

FlexDeploy is an intelligent deployment orchestration platform that uses AI to manage device categorization, analyze deployment failures, and optimize gating factors for ring-based deployment strategies.

**Key Capabilities:**
- 🤖 AI-powered device ring categorization
- 📊 Automated deployment failure analysis
- 🎛️ Natural language gating factor configuration
- 📈 Real-time deployment monitoring
- 🔄 Ring-based progressive rollout

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FlexDeploy System                        │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                │                               │
        ┌───────▼────────┐            ┌────────▼────────┐
        │   Frontend UI  │            │  Backend Server │
        │   (React App)  │            │   (FastAPI)     │
        │                │            │                 │
        │  - Material-UI │◄──REST────►│  - SQLite DB    │
        │  - Recharts    │   API      │  - Bedrock      │
        │  - Vite        │            │    Agents       │
        └────────────────┘            └─────────┬───────┘
         Port: 5173                             │
                                                │
                    ┌───────────────────────────┴────────────┐
                    │                                        │
            ┌───────▼────────┐                      ┌────────▼────────┐
            │  AWS Bedrock   │                      │   SQLite DB     │
            │                │                      │                 │
            │  Nova Pro v1   │                      │  - Devices      │
            │  Nova Lite v1  │                      │  - Deployments  │
            │                │                      │  - Rings        │
            │  Region:       │                      │  - Gating       │
            │  us-east-2     │                      │    Factors      │
            └────────────────┘                      └─────────────────┘
                    ▲
                    │
            ┌───────┴────────┐
            │  Credentials   │
            │ ~/.aws/        │
            │  credentials   │
            └────────────────┘
```

### Component Details

#### Frontend (React + Material-UI)
- **Dashboard**: Overview metrics and device distribution
- **Devices**: Device inventory with risk scores
- **Deployments**: Deployment management and execution
- **Rings**: Ring configuration and AI categorization
- **Deployment Details**: Ring-wise deployment status and failure analysis

#### Backend (FastAPI + Python)
- **REST API**: Device, deployment, and ring management
- **AI Agents**: Three specialized agents for intelligent operations
- **Database**: SQLite for persistent storage
- **Configuration**: Centralized config management

#### AI Agents (AWS Bedrock + Amazon Nova)

1. **Ring Categorization Agent**
   - Pipeline: prompt → SQL agent → reasoning agent → result
   - Automatically assigns devices to deployment rings
   
2. **Deployment Failure Agent**
   - Pipeline: gating factor → prompt → result
   - Analyzes failures and provides recommendations
   
3. **Gating Factor Agent**
   - Pipeline: user text → prompt → gating factor → result
   - Converts natural language to numeric thresholds

## ✨ Features

### Device Management
- Device inventory with comprehensive metrics
- Automatic risk score calculation
- Ring assignment (manual or AI-powered)
- Filter and search capabilities

### Deployment Management
- Create deployments with configurable gating factors
- Ring-based progressive rollout
- Real-time status tracking
- Start/stop deployment control

### Ring Configuration
- 4 default rings (Canary, Low Risk, High Risk, VIP)
- Custom categorization prompts
- Global gating factor configuration
- AI-powered device categorization

### AI-Powered Features
- Intelligent device ring assignment
- Automated failure root cause analysis
- Natural language gating factor parsing
- Validation and recommendations

### Dashboard & Monitoring
- Total devices, deployments, and active rings
- Device distribution visualization
- Real-time metrics

## 📦 Prerequisites

### Required Software

1. **Python 3.11 or higher**
   ```bash
   python3 --version
   ```

2. **Node.js 18 or higher**
   ```bash
   node --version
   ```

3. **npm or yarn**
   ```bash
   npm --version
   ```

4. **uv (Python package manager)**
   ```bash
   # Install uv
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

5. **AWS Account with Bedrock Access**
   - AWS account with IAM permissions
   - Amazon Nova models enabled
   - Valid credentials

### AWS Requirements

- **AWS Bedrock Access**: Must be enabled in your account
- **Model Access**: Amazon Nova Pro and Nova Lite
- **IAM Permissions**: `bedrock:InvokeModel`
- **Region**: us-east-1 (recommended for Bedrock)

## 🚀 Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/mmohanram13/flexDeploy.git
cd flexDeploy
```

### Step 2: Install Backend Dependencies

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Python packages
uv pip install -e .

# Alternatively, use pip
pip install -e .
```

**Backend packages installed:**
- fastapi >= 0.115.0
- uvicorn >= 0.32.0
- boto3 >= 1.35.0
- botocore >= 1.35.0
- strands-agents >= 1.12.0
- aiohttp >= 3.13.0

### Step 3: Install Frontend Dependencies

```bash
cd ui
npm install
cd ..
```

**Frontend packages installed:**
- react 19.1.1
- react-router-dom 7.9.4
- @mui/material 7.3.4
- @mui/icons-material 7.3.4
- recharts 3.2.1
- vite 5.0.4

### Step 4: Setup Configuration

```bash
# Run interactive setup
./setup_config.sh
```

This creates:
- `config.ini` - Application settings (SSO, regions, models)
- `~/.aws/credentials` - AWS credentials template

### Step 5: Configure AWS

#### Option A: Using AWS SSO (Recommended)

1. Edit `config.ini`:
```ini
[aws]
sso_start_url = https://your-org.awsapps.com/start/#
sso_region = us-east-2
bedrock_region = us-east-1
```

2. Get SSO credentials:
   - Visit your SSO start URL
   - Login and select account
   - Click "Command line or programmatic access"
   - Copy credentials to `~/.aws/credentials`

#### Option B: Using IAM User Keys

1. Create IAM user with Bedrock permissions
2. Generate access keys
3. Add to `~/.aws/credentials`:

```ini
[default]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
aws_session_token = IQoJb3JpZ2luX2VjEDY...  # Optional, required for SSO
```

### Step 6: Enable Bedrock Model Access

1. Login to AWS Console
2. Navigate to **AWS Bedrock** → **Model access**
3. Request access to:
   - Amazon Nova Pro (us.amazon.nova-pro-v1:0)
   - Amazon Nova Lite (us.amazon.nova-lite-v1:0)
4. Wait for approval (usually instant)

### Step 7: Verify Installation

```bash
# Test AWS Bedrock connection
python test_bedrock_agents.py
```

Expected output:
```
✓ Connection successful!
✓ Ring Categorization: PASSED
✓ Failure Analysis: PASSED
✓ Gating Factor Parsing: PASSED
✓ Gating Factor Validation: PASSED
```

## ⚙️ Configuration

### Configuration Files

#### config.ini (Application Settings)

Located in project root. Contains:

```ini
[aws]
# AWS SSO Configuration
sso_start_url = https://superopsglobalhackathon.awsapps.com/start/#
sso_region = us-east-2

# AWS Bedrock Configuration
bedrock_region = us-east-2
bedrock_model_pro = us.amazon.nova-pro-v1:0
bedrock_model_lite = us.amazon.nova-lite-v1:0

# Model Settings
default_max_tokens = 2000
default_temperature = 0.7

[server]
host = 0.0.0.0
port = 8000

[database]
db_name = flexdeploy.db
```

#### ~/.aws/credentials (AWS Credentials)

Located in home directory. Contains:

```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
aws_session_token = YOUR_SESSION_TOKEN  # Required for SSO
```

**Important**: 
- Never commit credentials to git
- Session tokens expire (refresh regularly with SSO)
- File permissions should be 600: `chmod 600 ~/.aws/credentials`

## 🎮 Running the Application

### Method 1: Run Both Services (Recommended)

```bash
# Start both UI and server simultaneously
./run_app.sh
```

This starts:
- Backend server on http://localhost:8000
- Frontend UI on http://localhost:5173

### Method 2: Run Separately

#### Start Backend Server

```bash
python -m server.main
```

Output:
```
✓ Database connected
✓ Configuration loaded
  - SSO Region: us-east-2
  - Bedrock Region: us-east-1
✓ AWS Bedrock agents initialized
  - Credentials from: ~/.aws/credentials
  - Configuration from: config.ini
INFO: Uvicorn running on http://0.0.0.0:8000
```

#### Start Frontend UI

```bash
cd ui
npm run dev
```

Output:
```
VITE v5.0.4  ready in 1234 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

### Accessing the Application

Open your browser to: **http://localhost:5173**

If the server is not running, you'll see a non-closable popup warning.

## 🤖 AI Agents

### 1. Ring Categorization Agent

**Purpose**: Automatically categorize devices into deployment rings

**Pipeline**: prompt → SQL agent → reasoning agent → result

**Usage**:
```bash
curl -X POST http://localhost:8000/api/ai/categorize-devices \
  -H "Content-Type: application/json" \
  -d '{"deviceIds": ["DEV-001", "DEV-002"]}'
```

**Response**:
```json
{
  "message": "Successfully categorized 2 devices",
  "categorizations": [
    {
      "deviceId": "DEV-001",
      "assignedRing": 1,
      "reasoning": "Device has stable metrics with CPU at 45% and memory at 60%, suitable for Ring 1 (Low Risk)"
    }
  ]
}
```

**Cost**: ~$0.0004 per device

### 2. Deployment Failure Agent

**Purpose**: Analyze why deployments failed

**Pipeline**: gating factor → prompt → result

**Usage**:
```bash
curl -X POST http://localhost:8000/api/ai/analyze-failure \
  -H "Content-Type: application/json" \
  -d '{
    "deploymentId": "DEP-001",
    "ringName": "Ring 1 - Low Risk Devices"
  }'
```

**Response**:
```json
{
  "deploymentId": "DEP-001",
  "ringName": "Ring 1 - Low Risk Devices",
  "analysis": "Primary failure reason: 15% of devices exceeded the CPU threshold of 80%..."
}
```

**Cost**: ~$0.004 per analysis

### 3. Gating Factor Agent

**Purpose**: Convert natural language to numeric gating factors

**Pipeline**: user text → prompt → gating factor → result

**Usage**:
```bash
curl -X POST http://localhost:8000/api/ai/gating-factors \
  -H "Content-Type: application/json" \
  -d '{
    "naturalLanguageInput": "Deploy only to very stable devices with low CPU usage"
  }'
```

**Response**:
```json
{
  "gatingFactors": {
    "avgCpuUsageMax": 60.0,
    "avgMemoryUsageMax": 70.0,
    "avgDiskFreeSpaceMin": 30.0,
    "riskScoreMin": 70,
    "riskScoreMax": 100
  },
  "explanation": "Conservative settings: CPU<60%, Memory<70%, Disk>30% for stable devices"
}
```

**Cost**: ~$0.0012 per request

### Cost Estimates

**Amazon Nova Pro** (default):
- Input: $0.0008 per 1K tokens
- Output: $0.0032 per 1K tokens

**Monthly estimate** (moderate usage):
- 1000 devices categorized: $0.40
- 50 failure analyses: $0.20
- 100 gating factor requests: $0.12
- **Total**: ~$0.72/month

## 📚 API Documentation

### Base URL

```
http://localhost:8000/api
```

### Endpoints

#### Devices

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/devices` | Get all devices |

#### Deployments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/deployments` | Get all deployments |
| POST | `/deployments` | Create new deployment |
| GET | `/deployments/{id}` | Get deployment details |
| POST | `/deployments/{id}/run` | Start deployment |
| POST | `/deployments/{id}/stop` | Stop deployment |

#### Rings

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/rings` | Get all rings |
| PUT | `/rings/{id}` | Update ring configuration |

#### Gating Factors

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/gating-factors` | Get default gating factors |
| PUT | `/gating-factors` | Update gating factors |

#### AI Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ai/categorize-devices` | AI device categorization |
| POST | `/ai/analyze-failure` | AI failure analysis |
| POST | `/ai/gating-factors` | Parse natural language |
| POST | `/ai/validate-gating-factors` | Validate thresholds |

#### Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/metrics` | Get dashboard metrics |
| GET | `/dashboard/device-distribution` | Get device distribution |

### Example API Calls

**Create Deployment**:
```bash
curl -X POST http://localhost:8000/api/deployments \
  -H "Content-Type: application/json" \
  -d '{
    "deploymentName": "Q4 Security Patch",
    "status": "Not Started",
    "gatingFactorMode": "default"
  }'
```

**Update Ring**:
```bash
curl -X PUT http://localhost:8000/api/rings/1 \
  -H "Content-Type: application/json" \
  -d '{
    "ringId": 1,
    "ringName": "Ring 1 - Low Risk",
    "categorizationPrompt": "Stable devices with good metrics"
  }'
```

## 📁 Project Structure

```
flexDeploy/
├── server/                      # Backend (Python/FastAPI)
│   ├── main.py                 # FastAPI server & API endpoints
│   ├── database.py             # SQLite database management
│   ├── bedrock_agents.py       # AWS Bedrock AI agents
│   ├── config.py               # Configuration management
│   └── flexdeploy.db           # SQLite database file
│
├── ui/                          # Frontend (React/Vite)
│   ├── src/
│   │   ├── App.jsx             # Main app component
│   │   ├── main.jsx            # Entry point
│   │   ├── api/
│   │   │   └── client.js       # API client
│   │   ├── components/
│   │   │   └── Layout.jsx      # Layout component
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx   # Dashboard page
│   │   │   ├── Devices.jsx     # Devices page
│   │   │   ├── Deployments.jsx # Deployments page
│   │   │   ├── DeploymentDetail.jsx
│   │   │   └── Rings.jsx       # Rings page
│   │   └── theme/
│   │       └── theme.js        # Material-UI theme
│   ├── package.json            # npm dependencies
│   └── vite.config.js          # Vite configuration
│
├── simulator/                   # Deployment simulator
│   ├── run_orchestrator.py    # Orchestrator
│   ├── src/
│   │   ├── master/             # Master node
│   │   └── slave/              # Agent nodes
│   └── examples/               # Example scripts
│
├── config.ini                   # Application configuration
├── config.ini.example          # Configuration template
├── pyproject.toml              # Python dependencies
├── run_app.sh                  # Start both UI & server
├── setup_config.sh             # Setup configuration
├── deploy_bedrock.sh           # Deploy with verification
├── test_bedrock_agents.py      # Test AI agents
└── README.md                   # This file
```

## 🔧 Troubleshooting

### Server Won't Start

**Problem**: Error loading configuration
```bash
# Verify config.ini exists
ls -la config.ini

# Create from template if missing
cp config.ini.example config.ini
```

**Problem**: AWS credentials not found
```bash
# Check credentials file
cat ~/.aws/credentials

# Verify permissions
chmod 600 ~/.aws/credentials

# Test AWS connection
aws sts get-caller-identity
```

**Problem**: Database error
```bash
# Check database exists
ls -la server/flexdeploy.db

# If corrupted, restore from backup
cp server/flexdeploy.db.backup server/flexdeploy.db
```

### UI Won't Load

**Problem**: "Server Not Running" popup
- Start the backend server: `python -m server.main`
- Verify it's running: `curl http://localhost:8000/`

**Problem**: npm packages missing
```bash
cd ui
rm -rf node_modules
npm install
```

**Problem**: Port 5173 already in use
```bash
# Kill existing process
lsof -ti:5173 | xargs kill -9

# Or use different port
npm run dev -- --port 3000
```

### AI Agents Not Working

**Problem**: "AI service not available"
```bash
# Test Bedrock connection
python test_bedrock_agents.py

# Check credentials are valid
aws sts get-caller-identity

# Verify Bedrock access
aws bedrock list-foundation-models --region us-east-1
```

**Problem**: "AccessDeniedException"
- Enable model access in AWS Console → Bedrock → Model access
- Request access to Amazon Nova Pro and Lite
- Verify IAM permissions include `bedrock:InvokeModel`

**Problem**: "Token expired"
- SSO tokens expire after 1-12 hours
- Refresh credentials:
  ```bash
  aws sso login
  # Or get new credentials from SSO portal
  ```

### Database Issues

**Problem**: Missing tables
```bash
# Check database integrity
sqlite3 server/flexdeploy.db ".tables"

# If tables missing, run migrations
python server/migrate_data.py
```

### Performance Issues

**Problem**: Slow AI responses
- Switch to Nova Lite for faster responses
- Edit `config.ini`:
  ```ini
  bedrock_model_pro = us.amazon.nova-lite-v1:0
  ```

**Problem**: High AWS costs
- Use batch operations instead of individual calls
- Implement caching for repeated queries
- Switch to Nova Lite model

## 🔒 Security

### Best Practices

1. **Never Commit Credentials**
   - `config.ini` is in `.gitignore`
   - `~/.aws/credentials` is in `.gitignore`
   - Review files before committing

2. **Secure File Permissions**
   ```bash
   chmod 600 ~/.aws/credentials
   chmod 644 config.ini
   ```

3. **Use AWS SSO**
   - Temporary credentials
   - Automatic expiration
   - Centralized access control

4. **Rotate Credentials**
   - SSO tokens expire automatically
   - Manual keys should rotate every 90 days

5. **Least Privilege IAM**
   ```json
   {
     "Effect": "Allow",
     "Action": ["bedrock:InvokeModel"],
     "Resource": [
       "arn:aws:bedrock:us-east-1::foundation-model/us.amazon.nova-*"
     ]
   }
   ```

6. **Environment Variables** (Production)
   ```bash
   export AWS_ACCESS_KEY_ID="..."
   export AWS_SECRET_ACCESS_KEY="..."
   ```

7. **Enable CloudTrail**
   - Track all Bedrock API calls
   - Monitor for unusual activity

### Production Deployment

For production, use IAM roles instead of credentials:

```python
# server/bedrock_agents.py
# No credentials needed - uses IAM role automatically
boto3.client('bedrock-runtime', region_name='us-east-1')
```

Deploy on:
- AWS EC2 with IAM role
- AWS ECS with task role
- AWS Lambda with execution role

## 🚀 Quick Start (TL;DR)

```bash
# 1. Install dependencies
uv pip install -e .
cd ui && npm install && cd ..

# 2. Setup configuration
./setup_config.sh

# 3. Edit AWS credentials
nano ~/.aws/credentials

# 4. Test Bedrock connection
python test_bedrock_agents.py

# 5. Run application
./run_app.sh

# 6. Open browser
# http://localhost:5173
```

## 📞 Support

### Getting Help

1. **Check logs**: Server logs show detailed error messages
2. **Test components**: Run `test_bedrock_agents.py` to verify AI agents
3. **Review configuration**: Ensure `config.ini` and `~/.aws/credentials` are correct
4. **Verify AWS**: Check Bedrock model access and IAM permissions

### Common Commands

```bash
# View configuration
python -c "from server.config import get_config; get_config().print_config()"

# Test database
sqlite3 server/flexdeploy.db "SELECT COUNT(*) FROM devices;"

# Check AWS credentials
aws configure list

# View server logs
python -m server.main 2>&1 | tee server.log

# Reinstall packages
uv pip install -e . --force-reinstall
cd ui && npm install --force && cd ..
```

## 🙏 Acknowledgments

- **AWS Bedrock** for AI infrastructure
- **Amazon Nova** models for intelligent analysis
- **Material-UI** for beautiful components
- **FastAPI** for high-performance backend
- **React** for modern frontend

