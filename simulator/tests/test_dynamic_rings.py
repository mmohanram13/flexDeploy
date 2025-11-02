"""
Quick Test Script for Dynamic Ring Assignment
Tests device status tracking and ring assignment functionality.
"""

import asyncio
import logging
from datetime import datetime

from src.common.messages import DeviceStatus, RingType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_device_status():
    """Test device status creation and methods."""
    logger.info("Testing DeviceStatus class...")
    
    # Create a healthy device
    device = DeviceStatus(
        slave_id="test-001",
        battery_level=80,
        battery_charging=False,
        cpu_usage=50.0,
        memory_usage=60.0,
        disk_usage=70.0,
        device_name="Test Device",
        os_version="Android 14",
        app_version="1.0.0"
    )
    
    assert device.is_healthy(), "Device should be healthy"
    logger.info(f"✓ Healthy device: Battery={device.battery_level}%, CPU={device.cpu_usage}%")
    
    # Create an unhealthy device (low battery)
    device2 = DeviceStatus(
        slave_id="test-002",
        battery_level=15,
        battery_charging=False,
        cpu_usage=50.0,
        memory_usage=60.0,
        disk_usage=70.0,
        device_name="Test Device 2"
    )
    
    assert not device2.is_healthy(), "Device should be unhealthy (low battery)"
    logger.info(f"✓ Unhealthy device (battery): Battery={device2.battery_level}%")
    
    # Create an unhealthy device (high CPU)
    device3 = DeviceStatus(
        slave_id="test-003",
        battery_level=80,
        battery_charging=False,
        cpu_usage=85.0,
        memory_usage=60.0,
        disk_usage=70.0,
        device_name="Test Device 3"
    )
    
    assert not device3.is_healthy(), "Device should be unhealthy (high CPU)"
    logger.info(f"✓ Unhealthy device (CPU): CPU={device3.cpu_usage}%")
    
    # Test update_metrics
    initial_battery = device.battery_level
    device.update_metrics()
    logger.info(f"✓ Metrics updated: Battery {initial_battery}% -> {device.battery_level}%")
    
    # Test serialization
    device_dict = device.to_dict()
    assert "slave_id" in device_dict
    assert "battery_level" in device_dict
    assert device_dict["assigned_ring"] == RingType.UNASSIGNED.value
    logger.info(f"✓ Serialization works: {list(device_dict.keys())}")
    
    # Test deserialization
    device_restored = DeviceStatus.from_dict(device_dict)
    assert device_restored.slave_id == device.slave_id
    assert device_restored.battery_level == device.battery_level
    logger.info(f"✓ Deserialization works: Restored device {device_restored.device_name}")
    
    logger.info("All DeviceStatus tests passed! ✓\n")


def test_ring_types():
    """Test ring type enum."""
    logger.info("Testing RingType enum...")
    
    assert RingType.CANARY.value == "canary"
    assert RingType.DEV.value == "dev"
    assert RingType.STAGE.value == "stage"
    assert RingType.PROD.value == "prod"
    assert RingType.UNASSIGNED.value == "unassigned"
    
    logger.info(f"✓ All ring types: {[r.value for r in RingType]}")
    
    # Test ring assignment
    device = DeviceStatus(
        slave_id="test-004",
        battery_level=90,
        battery_charging=True,
        cpu_usage=30.0,
        memory_usage=40.0,
        disk_usage=50.0,
        assigned_ring=RingType.PROD
    )
    
    assert device.assigned_ring == RingType.PROD
    logger.info(f"✓ Ring assignment works: {device.assigned_ring.value}")
    
    logger.info("All RingType tests passed! ✓\n")


async def test_integration():
    """Test basic integration with master and slaves."""
    logger.info("Testing integration...")
    
    from src.master.orchestrator import MasterOrchestrator
    from src.slave.agent import SlaveAgent
    from src.common import OrchestratorConfig, QueueManager
    
    # Create config
    config = OrchestratorConfig(
        master_id="test-master",
        slave_heartbeat_interval=2,
        use_aws_strands=False
    )
    
    # Create queue manager
    queue_manager = QueueManager(queue_type="memory")
    
    # Create master
    master = MasterOrchestrator(config=config)
    master_task = asyncio.create_task(master.start())
    await asyncio.sleep(1)
    
    logger.info("✓ Master orchestrator started")
    
    # Create slave
    slave = SlaveAgent(
        slave_id="test-slave-001",
        master_id="test-master",
        capabilities={"test": True},
        config=config,
        queue_manager=queue_manager,
        device_name="Test Device",
        os_version="Android 14"
    )
    
    slave_task = asyncio.create_task(slave.start())
    await asyncio.sleep(2)  # Wait for registration
    
    logger.info("✓ Slave agent started and registered")
    
    # Check if slave is registered
    assert "test-slave-001" in master.slaves, "Slave should be registered"
    logger.info(f"✓ Slave registered in master: {list(master.slaves.keys())}")
    
    # Check device status
    assert "test-slave-001" in master.device_statuses, "Device status should be stored"
    device = master.device_statuses["test-slave-001"]
    logger.info(f"✓ Device status tracked: {device.device_name}, Ring: {device.assigned_ring.value}")
    
    # Check ring assignment
    assert device.assigned_ring != RingType.UNASSIGNED, "Device should be assigned to a ring"
    logger.info(f"✓ Auto-assigned to ring: {device.assigned_ring.value}")
    
    # Test manual ring assignment
    await master.assign_slave_to_ring("test-slave-001", RingType.PROD, "Test assignment")
    await asyncio.sleep(1)
    
    assert slave.device_status.assigned_ring == RingType.PROD, "Slave should receive ring assignment"
    logger.info(f"✓ Manual ring assignment works: {slave.device_status.assigned_ring.value}")
    
    # Get cluster status
    status = await master.get_cluster_status()
    logger.info(f"✓ Cluster status: {status['total_slaves']} slaves, Ring dist: {status['ring_distribution']}")
    
    # Cleanup
    await slave.stop()
    await master.stop()
    slave_task.cancel()
    master_task.cancel()
    
    logger.info("All integration tests passed! ✓\n")


def main():
    """Run all tests."""
    logger.info("=" * 80)
    logger.info("Running Dynamic Ring Assignment Tests")
    logger.info("=" * 80 + "\n")
    
    # Run synchronous tests
    test_device_status()
    test_ring_types()
    
    # Run async integration test
    asyncio.run(test_integration())
    
    logger.info("=" * 80)
    logger.info("ALL TESTS PASSED! ✓")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
