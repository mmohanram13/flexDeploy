"""
Dynamic Ring Assignment Example
Demonstrates multiple slave agents with dynamic ring assignments based on device status.
"""

import asyncio
import logging
import random
from datetime import datetime

from src.master.orchestrator import MasterOrchestrator
from src.slave.agent import SlaveAgent
from src.common import (
    OrchestratorConfig,
    QueueManager,
    RingType,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def deployment_task_handler(parameters: dict):
    """Simulate a deployment task."""
    version = parameters.get("version", "1.0.0")
    package = parameters.get("package", "app")
    
    logger.info(f"Deploying {package} version {version}...")
    await asyncio.sleep(random.uniform(2, 5))  # Simulate deployment time
    
    return {
        "status": "success",
        "deployed_version": version,
        "deployed_at": datetime.now().isoformat()
    }


async def create_slave_agent(
    slave_id: str,
    master_id: str,
    config: OrchestratorConfig,
    queue_manager: QueueManager,
    device_name: str = None,
    os_version: str = None
):
    """Create and start a slave agent."""
    slave = SlaveAgent(
        slave_id=slave_id,
        master_id=master_id,
        capabilities={
            "deployment": True,
            "monitoring": True,
            "testing": True
        },
        config=config,
        queue_manager=queue_manager,
        device_name=device_name or f"Device-{slave_id[:8]}",
        os_version=os_version or f"Android {random.choice(['11', '12', '13', '14'])}",
        app_version="1.0.0"
    )
    
    # Register task handlers
    slave.register_task_handler("deployment", deployment_task_handler)
    slave.register_task_handler("update", deployment_task_handler)
    
    # Start slave in background
    asyncio.create_task(slave.start())
    
    return slave


async def monitor_cluster_status(master: MasterOrchestrator, interval: int = 10):
    """Monitor and display cluster status."""
    while master.running:
        try:
            await asyncio.sleep(interval)
            
            status = await master.get_cluster_status()
            
            logger.info("=" * 80)
            logger.info(f"CLUSTER STATUS UPDATE")
            logger.info(f"Total Slaves: {status['total_slaves']}")
            logger.info(f"Active Slaves: {status['active_slaves']}")
            logger.info(f"Idle Slaves: {status['idle_slaves']}")
            logger.info(f"Healthy Devices: {status['healthy_devices']}")
            logger.info(f"Total Tasks: {status['total_tasks']}")
            logger.info(f"Completed Tasks: {status['completed_tasks']}")
            logger.info(f"Failed Tasks: {status['failed_tasks']}")
            logger.info(f"Ring Distribution:")
            for ring, count in status['ring_distribution'].items():
                logger.info(f"  - {ring}: {count} devices")
            
            # Show individual slave details
            logger.info("\nSlave Details:")
            for slave_id, device in master.device_statuses.items():
                logger.info(
                    f"  {device.device_name} ({slave_id[:8]}): "
                    f"Ring={device.assigned_ring.value}, "
                    f"Battery={device.battery_level}%, "
                    f"CPU={device.cpu_usage:.1f}%, "
                    f"Healthy={device.is_healthy()}"
                )
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Error monitoring cluster: {e}")


async def submit_deployment_tasks(master: MasterOrchestrator, num_tasks: int = 5):
    """Submit deployment tasks to the cluster."""
    logger.info(f"Submitting {num_tasks} deployment tasks...")
    
    for i in range(num_tasks):
        await asyncio.sleep(2)  # Space out task submissions
        
        task_id = await master.submit_task(
            task_type="deployment",
            parameters={
                "version": f"1.{i}.0",
                "package": "myapp",
                "environment": random.choice(["dev", "stage", "prod"])
            },
            priority=random.randint(1, 10)
        )
        
        logger.info(f"Submitted task {i+1}/{num_tasks}: {task_id}")


async def manual_ring_reassignment(master: MasterOrchestrator):
    """Manually reassign some slaves to different rings."""
    await asyncio.sleep(15)  # Wait for initial setup
    
    while master.running:
        try:
            await asyncio.sleep(45)  # Every 45 seconds
            
            if not master.device_statuses:
                continue
            
            # Pick a random slave
            slave_id = random.choice(list(master.device_statuses.keys()))
            device = master.device_statuses[slave_id]
            
            # Pick a new ring (different from current)
            available_rings = [r for r in [RingType.CANARY, RingType.DEV, RingType.STAGE, RingType.PROD] 
                             if r != device.assigned_ring]
            
            if available_rings:
                new_ring = random.choice(available_rings)
                await master.assign_slave_to_ring(
                    slave_id,
                    new_ring,
                    "Manual reassignment for demonstration"
                )
                logger.info(
                    f"Manually reassigned {device.device_name} from "
                    f"{device.assigned_ring.value} to {new_ring.value}"
                )
        
        except Exception as e:
            logger.error(f"Error in manual reassignment: {e}")


async def main():
    """Main function to run the dynamic ring assignment example."""
    logger.info("Starting Dynamic Ring Assignment Example")
    logger.info("=" * 80)
    
    # Create configuration
    config = OrchestratorConfig(
        master_id="master-orchestrator",
        slave_heartbeat_interval=5,
        slave_timeout=30,
        task_queue_size=100,
        use_aws_strands=False,  # Set to True if you have AWS Strands configured
        log_level="INFO"
    )
    
    # Create queue manager
    queue_manager = QueueManager(queue_type="memory")
    
    # Create and start master orchestrator
    logger.info("Creating master orchestrator...")
    master = MasterOrchestrator(config=config)
    
    # Start master in background
    master_task = asyncio.create_task(master.start())
    await asyncio.sleep(2)  # Give master time to start
    
    # Create multiple slave agents with different characteristics
    logger.info("Creating slave agents...")
    slaves = []
    
    device_types = [
        ("Pixel 8 Pro", "Android 14"),
        ("Galaxy S23", "Android 13"),
        ("OnePlus 11", "Android 13"),
        ("iPhone 15", "iOS 17"),
        ("Pixel 7", "Android 13"),
        ("Galaxy Tab S9", "Android 13"),
        ("iPad Pro", "iOS 17"),
        ("Motorola Edge", "Android 12"),
    ]
    
    for i, (device_name, os_version) in enumerate(device_types):
        slave_id = f"slave-{i+1:03d}-{random.randint(1000, 9999)}"
        slave = await create_slave_agent(
            slave_id=slave_id,
            master_id=config.master_id,
            config=config,
            queue_manager=queue_manager,
            device_name=device_name,
            os_version=os_version
        )
        slaves.append(slave)
        await asyncio.sleep(0.5)  # Space out registrations
    
    logger.info(f"Created {len(slaves)} slave agents")
    
    # Start background tasks
    monitor_task = asyncio.create_task(monitor_cluster_status(master, interval=15))
    task_submission_task = asyncio.create_task(submit_deployment_tasks(master, num_tasks=10))
    reassignment_task = asyncio.create_task(manual_ring_reassignment(master))
    
    # Run for a while
    try:
        logger.info("Running cluster for 120 seconds...")
        await asyncio.sleep(120)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    
    # Cleanup
    logger.info("Shutting down cluster...")
    monitor_task.cancel()
    reassignment_task.cancel()
    
    for slave in slaves:
        await slave.stop()
    
    await master.stop()
    master_task.cancel()
    
    # Final status
    final_status = await master.get_cluster_status()
    logger.info("\n" + "=" * 80)
    logger.info("FINAL CLUSTER STATUS")
    logger.info(f"Total Tasks Completed: {final_status['completed_tasks']}")
    logger.info(f"Total Tasks Failed: {final_status['failed_tasks']}")
    logger.info(f"Final Ring Distribution:")
    for ring, count in final_status['ring_distribution'].items():
        logger.info(f"  - {ring}: {count} devices")
    logger.info("=" * 80)
    
    logger.info("Example completed!")


if __name__ == "__main__":
    asyncio.run(main())
