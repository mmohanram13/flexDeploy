"""
QUICKSTART: Dynamic Ring Assignment with Multiple Slaves
=========================================================

This script demonstrates how to quickly set up and run a master-slave
orchestrator with dynamic ring assignment for multiple devices.

Features demonstrated:
- Creating multiple slave agents with different device characteristics
- Automatic ring assignment based on device health
- Real-time device status monitoring
- Dynamic ring rebalancing
- Task distribution across rings

Run this script to see the system in action!
"""

import asyncio
import logging
from datetime import datetime

from src.master.orchestrator import MasterOrchestrator
from src.slave.agent import SlaveAgent
from src.common import OrchestratorConfig, QueueManager, RingType

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def simple_task_handler(parameters: dict):
    """Simple task handler for demonstration."""
    task_name = parameters.get("name", "unnamed")
    await asyncio.sleep(1)  # Simulate work
    return {"status": "success", "task": task_name}


async def main():
    print("\n" + "=" * 80)
    print("QUICKSTART: Dynamic Ring Assignment System")
    print("=" * 80 + "\n")
    
    # Step 1: Create configuration
    print("Step 1: Creating configuration...")
    config = OrchestratorConfig(
        master_id="master",
        slave_heartbeat_interval=5,
        use_aws_strands=False  # Set to True if AWS Strands is configured
    )
    print("✓ Configuration created\n")
    
    # Step 2: Create queue manager
    print("Step 2: Creating message queue...")
    queue_manager = QueueManager(queue_type="memory")
    print("✓ Queue manager created\n")
    
    # Step 3: Start master orchestrator
    print("Step 3: Starting master orchestrator...")
    master = MasterOrchestrator(config=config)
    asyncio.create_task(master.start())
    await asyncio.sleep(1)
    print("✓ Master orchestrator running\n")
    
    # Step 4: Create and start multiple slaves
    print("Step 4: Creating 5 slave agents...")
    slaves = []
    
    devices = [
        ("Pixel 8", "Android 14"),
        ("Galaxy S23", "Android 13"),
        ("iPhone 15", "iOS 17"),
        ("OnePlus 11", "Android 13"),
        ("Pixel Tablet", "Android 14"),
    ]
    
    for i, (device_name, os_version) in enumerate(devices):
        slave = SlaveAgent(
            slave_id=f"slave-{i+1:03d}",
            master_id="master",
            capabilities={"deployment": True, "testing": True},
            config=config,
            queue_manager=queue_manager,
            device_name=device_name,
            os_version=os_version,
            app_version="1.0.0"
        )
        
        # Register task handler
        slave.register_task_handler("demo_task", simple_task_handler)
        
        # Start slave
        asyncio.create_task(slave.start())
        slaves.append(slave)
        
        print(f"  ✓ Created {device_name}")
        await asyncio.sleep(0.5)
    
    print(f"✓ All {len(slaves)} slaves started and registered\n")
    
    # Step 5: Wait for registration and ring assignment
    print("Step 5: Waiting for ring assignments...")
    await asyncio.sleep(3)
    print("✓ Ring assignments complete\n")
    
    # Step 6: Display cluster status
    print("Step 6: Cluster Status")
    print("-" * 80)
    status = await master.get_cluster_status()
    print(f"Total Slaves: {status['total_slaves']}")
    print(f"Healthy Devices: {status['healthy_devices']}")
    print(f"\nRing Distribution:")
    for ring, count in status['ring_distribution'].items():
        print(f"  {ring.upper()}: {count} devices")
    
    print(f"\nDevice Details:")
    for slave_id, device in master.device_statuses.items():
        health_icon = "✓" if device.is_healthy() else "⚠"
        print(f"  {health_icon} {device.device_name}")
        print(f"    Ring: {device.assigned_ring.value}")
        print(f"    Battery: {device.battery_level}%, CPU: {device.cpu_usage:.1f}%")
    print("-" * 80 + "\n")
    
    # Step 7: Submit some tasks
    print("Step 7: Submitting 3 tasks...")
    for i in range(3):
        task_id = await master.submit_task(
            task_type="demo_task",
            parameters={"name": f"Task-{i+1}"},
            priority=i
        )
        print(f"  ✓ Submitted Task-{i+1}: {task_id[:8]}...")
    print()
    
    # Step 8: Run for 20 seconds
    print("Step 8: Monitoring cluster (20 seconds)...")
    for i in range(4):
        await asyncio.sleep(5)
        status = await master.get_cluster_status()
        print(f"  [{i*5+5}s] Completed: {status['completed_tasks']}, "
              f"Active: {status['active_slaves']}, "
              f"Idle: {status['idle_slaves']}")
    print()
    
    # Step 9: Demonstrate manual ring assignment
    print("Step 9: Manual ring reassignment...")
    if master.device_statuses:
        slave_id = list(master.device_statuses.keys())[0]
        device = master.device_statuses[slave_id]
        print(f"  Moving {device.device_name} to PROD ring...")
        await master.assign_slave_to_ring(slave_id, RingType.PROD, "Demo assignment")
        await asyncio.sleep(1)
        print(f"  ✓ {device.device_name} now in {device.assigned_ring.value} ring\n")
    
    # Step 10: Final status
    print("Step 10: Final Status")
    print("-" * 80)
    final_status = await master.get_cluster_status()
    print(f"Tasks Completed: {final_status['completed_tasks']}")
    print(f"Tasks Failed: {final_status['failed_tasks']}")
    print(f"Ring Distribution:")
    for ring, count in final_status['ring_distribution'].items():
        print(f"  {ring.upper()}: {count} devices")
    print("-" * 80 + "\n")
    
    # Cleanup
    print("Cleaning up...")
    for slave in slaves:
        await slave.stop()
    await master.stop()
    print("✓ Cleanup complete\n")
    
    print("=" * 80)
    print("QUICKSTART COMPLETE!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Check out DYNAMIC_RING_ASSIGNMENT.md for detailed documentation")
    print("2. Run examples/dynamic_ring_assignment.py for advanced features")
    print("3. Customize device health criteria in src/common/messages.py")
    print("4. Implement your own task handlers and deployment logic")
    print("\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
