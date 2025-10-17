"""Basic example demonstrating the master-slave orchestrator."""

import asyncio
import logging
from src import (
    MasterOrchestrator,
    SlaveAgent,
    OrchestratorConfig,
    QueueManager,
)
from src.ui.handlers import add_asset


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Example task handlers
async def process_data_task(parameters: dict) -> dict:
    """Example task handler for data processing."""
    data = parameters.get("data", [])
    operation = parameters.get("operation", "sum")
    
    logger.info(f"Processing data with operation: {operation}")
    await asyncio.sleep(1)  # Simulate work
    
    if operation == "sum":
        result = sum(data)
    elif operation == "multiply":
        result = 1
        for x in data:
            result *= x
    else:
        result = None
    
    return {"result": result, "operation": operation}


async def analyze_metrics_task(parameters: dict) -> dict:
    """Example task handler for metrics analysis."""
    metrics = parameters.get("metrics", {})
    
    logger.info(f"Analyzing metrics: {list(metrics.keys())}")
    await asyncio.sleep(2)  # Simulate work
    
    analysis = {
        "summary": {
            "total_metrics": len(metrics),
            "avg_value": sum(metrics.values()) / len(metrics) if metrics else 0
        }
    }
    
    return analysis


async def fetch_data_task(parameters: dict) -> dict:
    """Example task handler for data fetching."""
    source = parameters.get("source", "unknown")
    
    logger.info(f"Fetching data from: {source}")
    await asyncio.sleep(1.5)  # Simulate work
    
    return {
        "source": source,
        "data": [1, 2, 3, 4, 5],
        "timestamp": "2025-10-13T00:00:00"
    }


async def main():
    """Main example demonstrating the orchestrator."""
    
    # Create configuration
    config = OrchestratorConfig(
        master_id="master-001",
        slave_heartbeat_interval=5,
        task_timeout=60,
        use_aws_strands=False  # Set to True if AWS credentials are configured
    )
    
    # Create shared queue manager
    queue_manager = QueueManager(queue_type="memory", maxsize=100)
    
    # Create master orchestrator
    master = MasterOrchestrator(config)
    
    # Create slave agents
    slave1 = SlaveAgent(
        slave_id="slave-001",
        master_id=config.master_id,
        capabilities={"tasks": ["process_data", "analyze_metrics"]},
        config=config,
        queue_manager=queue_manager
    )
    
    slave2 = SlaveAgent(
        slave_id="slave-002",
        master_id=config.master_id,
        capabilities={"tasks": ["fetch_data", "process_data"]},
        config=config,
        queue_manager=queue_manager
    )
    
    # Register task handlers
    slave1.register_task_handler("process_data", process_data_task)
    slave1.register_task_handler("analyze_metrics", analyze_metrics_task)
    slave2.register_task_handler("fetch_data", fetch_data_task)
    slave2.register_task_handler("process_data", process_data_task)
    
    # Share queue manager with master
    master.queue_manager = queue_manager
    
    logger.info("=" * 80)
    logger.info("Starting Master-Slave Orchestrator Example")
    logger.info("=" * 80)
    
    # Start agents in background
    master_task = asyncio.create_task(master.start())
    slave1_task = asyncio.create_task(slave1.start())
    slave2_task = asyncio.create_task(slave2.start())
    
    # Wait for registration
    await asyncio.sleep(2)
    
    logger.info("\n" + "=" * 80)
    logger.info("Submitting tasks to master orchestrator")
    logger.info("=" * 80)
    
    # Submit various tasks
    tasks = []
    
    # Task 1: Process data
    task1_id = await master.submit_task(
        "process_data",
        {"data": [1, 2, 3, 4, 5], "operation": "sum"},
        priority=1
    )
    tasks.append(task1_id)
    
    # Task 2: Fetch data
    task2_id = await master.submit_task(
        "fetch_data",
        {"source": "database"},
        priority=2
    )
    tasks.append(task2_id)
    
    # Task 3: Analyze metrics
    task3_id = await master.submit_task(
        "analyze_metrics",
        {"metrics": {"cpu": 45.2, "memory": 68.5, "disk": 32.1}},
        priority=1
    )
    tasks.append(task3_id)
    
    # Task 4: Process data (multiply)
    task4_id = await master.submit_task(
        "process_data",
        {"data": [2, 3, 4], "operation": "multiply"},
        priority=0
    )
    tasks.append(task4_id)
    
    logger.info(f"\nSubmitted {len(tasks)} tasks")
    
    # Wait for tasks to complete
    logger.info("\n" + "=" * 80)
    logger.info("Waiting for tasks to complete...")
    logger.info("=" * 80)
    
    await asyncio.sleep(10)
    
    # Check cluster status
    logger.info("\n" + "=" * 80)
    logger.info("Cluster Status")
    logger.info("=" * 80)
    
    status = await master.get_cluster_status()
    logger.info(f"\nMaster ID: {status['master_id']}")
    logger.info(f"Total Slaves: {status['total_slaves']}")
    logger.info(f"Active Slaves: {status['active_slaves']}")
    logger.info(f"Idle Slaves: {status['idle_slaves']}")
    logger.info(f"\nTotal Tasks: {status['total_tasks']}")
    logger.info(f"Pending: {status['pending_tasks']}")
    logger.info(f"In Progress: {status['in_progress_tasks']}")
    logger.info(f"Completed: {status['completed_tasks']}")
    logger.info(f"Failed: {status['failed_tasks']}")
    
    # Check individual task results
    logger.info("\n" + "=" * 80)
    logger.info("Task Results")
    logger.info("=" * 80)
    
    for task_id in tasks:
        task_status = await master.get_task_status(task_id)
        if task_status:
            logger.info(f"\nTask ID: {task_id[:8]}...")
            logger.info(f"  Type: {task_status['task_type']}")
            logger.info(f"  Status: {task_status['status']}")
            logger.info(f"  Assigned to: {task_status['assigned_to']}")
            if task_status['result']:
                logger.info(f"  Result: {task_status['result']}")
    
    # Shutdown
    logger.info("\n" + "=" * 80)
    logger.info("Shutting down orchestrator")
    logger.info("=" * 80)
    
    await master.stop()
    await slave1.stop()
    await slave2.stop()
    
    # Cancel background tasks
    master_task.cancel()
    slave1_task.cancel()
    slave2_task.cancel()
    
    try:
        await asyncio.gather(master_task, slave1_task, slave2_task)
    except asyncio.CancelledError:
        pass
    
    logger.info("\nExample completed successfully!")
    
    # start master (this spawns config.default_num_agents agents by default)
    await master.start()

    # simulate UI adding an asset - this will spawn one additional agent
    add_asset(master, {"asset_id": "asset-001", "type": "device"})

    # keep running for a short demo so heartbeats are printed
    await asyncio.sleep(12)

    # stop agents cleanly
    await master.stop_all_agents()

if __name__ == "__main__":
    asyncio.run(main())
