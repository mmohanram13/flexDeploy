# FlexDeploy - AI based RMM Deployment Orchestrator

An intelligent deployment orchestration system with master-slave agent architecture powered by AWS Strands.

## 🎯 Project Components

### 1. UI (React + Material-UI)
- Modern deployment dashboard
- Device management with AI risk scoring
- Ring-based deployment visualization
- Real-time monitoring and status tracking

**Location**: `ui/`

### 2. AWS Orchestrator (Python + Strands)
- Master-slave agent architecture
- Distributed task execution
- AI-powered decision making with AWS Strands
- Priority-based task scheduling
- Health monitoring and auto-recovery

**Location**: `aws-orchestrator/`

## 🚀 Quick Start

### Run UI
```bash
cd ui
npm install
npm run dev
```
Access at: http://localhost:5173

### Run Orchestrator Examples
```bash
cd aws-orchestrator
python examples/basic_example.py
python examples/flexdeploy_integration.py
```

## 📖 Documentation

- [UI Documentation](ui/README.md)
- [Orchestrator Documentation](aws-orchestrator/README.md)
- [Orchestrator Quick Start](aws-orchestrator/GETTING_STARTED.md)

## 🏗️ Architecture

```
FlexDeploy
├── UI (React)
│   ├── Dashboard
│   ├── Devices
│   ├── Deployments
│   ├── Rings Config
│   └── Settings
│
└── AWS Orchestrator (Python)
    ├── Master Agent (Coordinator)
    ├── Slave Agents (Workers)
    │   ├── Risk Analyzer
    │   ├── Deployment Executor
    │   └── Health Monitor
    └── Message Queue (Communication)
```

## 🤖 AWS Strands Integration

The orchestrator leverages AWS Strands for:
- Intelligent task routing
- Risk assessment and prediction
- Resource optimization
- Adaptive retry strategies
- Deployment decision making

## 🚀 Future Improvements Roadmap

- AI Chat-Based Deployment Customization
- Manual Override Capabilities
- Advanced Device Management 
- External Factor Analysis and Provide Deployment Success Strategy Before Deployment
- Compliance & Audit Logs
- Automated Rollback Capabilities

---

**Note**: These features are intentionally excluded from the hackathon MVP to maintain focus on the core innovation: **Automatic ring creation and metric-based autonomous gating**.
