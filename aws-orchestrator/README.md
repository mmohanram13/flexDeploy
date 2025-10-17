# AWS Orchestrator - Master-Slave Agent System

A powerful master-slave agent orchestration system built with AWS Strands package for coordinating distributed tasks and AI-powered decision making.

## 🚀 Features

- **Master-Slave Architecture**: Centralized master orchestrator coordinating multiple slave agents
- **AWS Strands Integration**: Built-in support for Amazon Nova Act AI model
- **Dynamic Ring Assignment**: Intelligent deployment ring management based on device health
- **Device Status Tracking**: Real-time monitoring of battery, CPU, memory, and disk usage
- **Task Queue Management**: Efficient task distribution with priority-based scheduling
- **Heartbeat Monitoring**: Automatic slave health monitoring with timeout detection
- **Task Retry Logic**: Automatic retry for failed tasks with configurable limits
- **Message Passing**: Reliable message-based communication between agents
- **Scalable Design**: Easily add or remove slave agents dynamically
- **Automatic Rebalancing**: Dynamic ring rebalancing based on device health metrics
- **Status Tracking**: Real-time monitoring of cluster and task status
- **Error Handling**: Robust error handling and recovery mechanisms

## 📁 Project Structure

```
aws-orchestrator/
├── src/
│   ├── common/
│   │   ├── __init__.py
│   │   ├── messages.py      # Message types and data structures
│   │   ├── config.py        # Configuration management
│   │   └── queue.py         # Message queue implementations
│   ├── master/
│   │   ├── __init__.py
│   │   └── orchestrator.py  # Master orchestrator agent
│   ├── slave/
│   │   ├── __init__.py
│   │   └── agent.py         # Slave agent implementation
│   └── __init__.py
├── examples/
│   ├── basic_example.py     # Basic usage example
│   └── advanced_example.py  # Advanced AI-powered example
├── run_orchestrator.py      # Main entry point to run the service
├── tests/
│   └── test_orchestrator.py # Unit tests
├── README.md
└── requirements.txt
```

## 🛠️ Installation

### Prerequisites

- Python 3.11+
- AWS credentials configured (optional, for AWS Strands features)

### Install Dependencies

```bash
# Create a virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 📖 How to Run the Project

### Running the Orchestrator Service

The project provides a simple HTTP API server for interacting with the orchestrator:

```bash
# From the aws-orchestrator directory
python run_orchestrator.py
```

This will:
1. Start the master orchestrator
2. Spawn 2 default slave agents
3. Simulate adding an asset (which spawns 1 additional agent)
4. Start the HTTP server on port 8000

You should see output like:
```
Starting master orchestrator (background)...
Spawning 2 default agents...
[Master] spawned agent slave-12345678
[Master] spawned agent slave-87654321
Simulating asset add from UI (will spawn one agent)...
[Master] spawned agent slave-abcdef12
Orchestrator is running. HTTP API will accept commands...
HTTP API running at http://0.0.0.0:8000
```

### API Endpoints

The orchestrator exposes the following HTTP endpoints:

#### GET Endpoints

- `GET /cluster_status` - Get overall status of the orchestrator cluster
- `GET /list_agents` - List all agent IDs
- `GET /status/{task_id}` - Get status of a specific task
- `GET /deployment_status?deployment_id=xyz` - Get status of a deployment
- `GET /asset_details` - Get all assets with their associated agents
- `GET /asset_details?asset_id=xyz` - Get details for a specific asset

#### POST Endpoints

- `POST /spawn_agent` - Create a new agent with random details
- `POST /add_asset` - Add a new asset and spawn an agent to manage it
- `POST /submit_task` - Submit a task for execution
- `POST /start_deployment` - Begin a deployment process
- `POST /complete_deployment` - Mark a deployment as complete
- `POST /simulate_activity` - Test endpoint to simulate metric changes

### Example API Usage

#### Start a Deployment

```bash
curl -X POST http://localhost:8000/start_deployment \
  -H "Content-Type: application/json" \
  -d '{"deployment_id": "deploy-001"}'
```

This will:
- Mark deployment as active
- Randomly select 30-50% of agents
- Instruct selected agents to modify their metrics (CPU, memory, battery)
- Return the affected agents in the response

#### Check Deployment Status

```bash
curl http://localhost:8000/deployment_status?deployment_id=deploy-001
```

#### Complete a Deployment

```bash
curl -X POST http://localhost:8000/complete_deployment \
  -H "Content-Type: application/json" \
  -d '{"deployment_id": "deploy-001"}'
```

This will:
- Mark deployment as complete
- Instruct 40-80% of agents to recover their metrics
- Return complete deployment status with all agent and asset details

#### Add an Asset

```bash
curl -X POST http://localhost:8000/add_asset \
  -H "Content-Type: application/json" \
  -d '{
    "id": "7712...328",
    "name": "LAPTOP-RCK72RHH",
    "manufacturer": "LENOVO",
    "model": "IdeaPad Slim 5",
    "osName": "Win 11 Home",
    "site": "Coimbatore",
    "department": "Marketing"
  }'
```

## 🌐 Deployment Options

### Local Development
- Run as shown above using `python run_orchestrator.py`

### AWS EC2/ECS
- Deploy using Docker:
  ```dockerfile
  FROM python:3.11
  WORKDIR /app
  COPY . .
  RUN pip install -r requirements.txt
  EXPOSE 8000
  CMD ["python", "run_orchestrator.py"]
  ```

### AWS Lambda
The application is Lambda-compatible using the Mangum adapter:
1. Install `mangum`: `pip install mangum`
2. Deploy the application as a Lambda function
3. Set the handler to: `run_orchestrator.lambda_handler`
4. Configure API Gateway to route requests to the Lambda function

## 🏗️ Architecture

### Master Orchestrator

The master orchestrator is responsible for:
- Managing slave agent registration and lifecycle
- Distributing tasks to available slaves
- Monitoring slave health via heartbeats
- Tracking task status and results
- Handling task failures and retries
- Providing cluster status information

### Slave Agent

Slave agents are responsible for:
- Registering with the master
- Sending periodic heartbeats with device metrics
- Receiving and executing tasks
- Modifying metrics when instructed by the master
- Reporting task progress and results
- Handling errors gracefully

### Deployment Process

When a deployment is started:
1. Master selects 30-50% of agents randomly
2. Selected agents modify their metrics:
   - CPU usage increases by 10-50%
   - Memory usage increases by 10-30%
   - Battery decreases by 5-15% (if not charging)
3. These changes persist until the deployment is completed
4. On completion, 40-80% of agents recover toward normal metrics

## 🧪 Testing

### Using the Simulation Endpoint

To manually trigger agent metric changes:

```bash
curl -X POST http://localhost:8000/simulate_activity
```

## 📊 Use Cases

### 1. Device Fleet Monitoring

Monitor a fleet of devices during deployment windows to ensure health metrics stay within acceptable ranges.

### 2. AI-Powered Deployment

Use the built-in simulation capabilities to test deployment strategies and predict potential issues.

### 3. Risk Analysis

Analyze which devices are most affected by deployments and adjust ring assignments accordingly.

## 🚦 Status and Monitoring

Track deployment status via the API and monitor agent metrics in real-time.

## 🤝 Contributing

Contributions welcome! This is a hackathon MVP focusing on core orchestration capabilities.

---

**Built with AWS Strands for intelligent agent orchestration** 🤖
