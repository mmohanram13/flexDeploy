"""AWS Orchestrator Package - Quick Start Guide."""

print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║              AWS Orchestrator - Master-Slave Agent System                ║
║                   Built with AWS Strands Package                         ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

🚀 QUICK START GUIDE

1. Run Basic Example:
   python examples/basic_example.py

2. Run Advanced AI Example:
   python examples/advanced_example.py

3. Run FlexDeploy Integration:
   python examples/flexdeploy_integration.py

4. Run Tests:
   python tests/test_orchestrator.py

📖 DOCUMENTATION

See README.md for complete documentation and API reference.

🏗️ ARCHITECTURE

┌─────────────────┐
│  Master Agent   │ ← Coordinates and manages slave agents
│  (Orchestrator) │ ← Distributes tasks with priority
└────────┬────────┘ ← Monitors health and status
         │
    ┌────┴─────┬──────────┬──────────┐
    │          │          │          │
┌───▼───┐  ┌──▼────┐  ┌──▼────┐  ┌──▼────┐
│Slave-1│  │Slave-2│  │Slave-3│  │Slave-N│
│       │  │       │  │       │  │       │
│Execute│  │Execute│  │Execute│  │Execute│
│Tasks  │  │Tasks  │  │Tasks  │  │Tasks  │
└───────┘  └───────┘  └───────┘  └───────┘

🎯 KEY FEATURES

✓ Master-slave architecture with centralized coordination
✓ AWS Strands integration for AI-powered decision making
✓ Priority-based task queue management
✓ Automatic health monitoring with heartbeats
✓ Task retry logic with configurable limits
✓ Real-time status tracking and monitoring
✓ Scalable design - add/remove slaves dynamically
✓ Robust error handling and recovery

💡 USE CASES

• Distributed data processing
• AI-powered deployment orchestration
• Parallel task execution
• Health monitoring and alerting
• Risk analysis and optimization
• Report generation

🔧 CONFIGURATION

Edit src/common/config.py or pass OrchestratorConfig:

    config = OrchestratorConfig(
        master_id="my-master",
        slave_heartbeat_interval=5,
        task_timeout=60,
        use_aws_strands=True
    )

📝 EXAMPLE CODE

from src import MasterOrchestrator, SlaveAgent, OrchestratorConfig

# Create master and slave
master = MasterOrchestrator(config)
slave = SlaveAgent(slave_id="worker-1", ...)

# Register task handler
slave.register_task_handler("my_task", handler_function)

# Submit task
task_id = await master.submit_task("my_task", params)

# Get result
result = await master.get_task_status(task_id)

🤝 INTEGRATION

This orchestrator is designed to work with FlexDeploy's AI-powered
deployment system. See examples/flexdeploy_integration.py for details.

📊 MONITORING

Check cluster status:
    status = await master.get_cluster_status()
    
View task status:
    task = await master.get_task_status(task_id)

⚙️ REQUIREMENTS

• Python 3.11+
• strands-agents >= 1.12.0
• strands-agents-tools >= 0.2.11

Happy orchestrating! 🎉
""")
