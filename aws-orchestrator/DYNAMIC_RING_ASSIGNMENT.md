# Dynamic Ring Assignment System

## Overview

The AWS Strands Master-Slave Orchestrator now includes a sophisticated **Dynamic Ring Assignment System** that automatically manages device deployment rings based on real-time device health metrics.

## Features

### 1. Device Status Tracking

Each slave agent maintains comprehensive device status information:

- **Battery Status**: Level (0-100%) and charging state
- **CPU Usage**: Real-time CPU utilization (0-100%)
- **Memory Usage**: RAM utilization (0-100%)
- **Disk Usage**: Storage utilization (0-100%)
- **Ring Assignment**: Current deployment ring
- **Device Metadata**: Name, OS version, app version

### 2. Deployment Rings

The system supports four deployment rings for progressive rollout:

| Ring     | Purpose                      | Characteristics                          |
|----------|------------------------------|------------------------------------------|
| CANARY   | Early testing                | Small subset, experimental updates       |
| DEV      | Development testing          | Development devices, unstable builds     |
| STAGE    | Pre-production validation    | Stable builds, final testing             |
| PROD     | Production deployment        | Fully validated, production-ready builds |

### 3. Automatic Ring Assignment

The master orchestrator automatically assigns slaves to rings based on:

- **Device Health**: Battery level, CPU usage, memory usage
- **Load Distribution**: Balanced distribution across rings
- **Health-Based Rules**:
  - Healthy devices (Battery > 20%, CPU < 80%, Memory < 85%) can be assigned to any ring
  - Unhealthy devices are restricted to CANARY or DEV rings

### 4. Dynamic Rebalancing

The system includes an intelligent rebalancer that:

- Runs every 30 seconds
- Moves unhealthy devices out of PROD
- Randomly redistributes devices for load balancing (10% chance per check)
- Maintains cluster health and optimal distribution

## Architecture

### Device Status Updates

```
Slave Agent → Device Status → Master Orchestrator
     ↓                              ↓
 Update Metrics              Store & Analyze
     ↓                              ↓
 Send Heartbeat              Rebalancing Logic
     ↓                              ↓
 Send Status Update          Ring Assignment
```

### Ring Assignment Flow

```
1. Slave registers with Master
2. Master evaluates device health
3. Auto-assign to appropriate ring
4. Send ring assignment message
5. Slave receives and updates status
6. Continue monitoring and rebalancing
```

## Usage Examples

### Basic Usage

```python
import asyncio
from src.master.orchestrator import MasterOrchestrator
from src.slave.agent import SlaveAgent
from src.common import OrchestratorConfig, QueueManager, RingType

# Create configuration
config = OrchestratorConfig(
    master_id="master-orchestrator",
    slave_heartbeat_interval=5,
)

# Create queue manager
queue_manager = QueueManager(queue_type="memory")

# Create master
master = MasterOrchestrator(config=config)
asyncio.create_task(master.start())

# Create slave with device info
slave = SlaveAgent(
    slave_id="slave-001",
    master_id="master-orchestrator",
    capabilities={"deployment": True},
    config=config,
    queue_manager=queue_manager,
    device_name="Pixel 8 Pro",
    os_version="Android 14",
    app_version="1.0.0"
)

# Start slave (will auto-register and get ring assignment)
await slave.start()
```

### Manual Ring Assignment

```python
# Assign specific slave to PROD ring
await master.assign_slave_to_ring(
    slave_id="slave-001",
    ring=RingType.PROD,
    reason="Promoted to production after successful staging"
)
```

### Query Cluster Status

```python
# Get comprehensive cluster status
status = await master.get_cluster_status()

print(f"Total Slaves: {status['total_slaves']}")
print(f"Healthy Devices: {status['healthy_devices']}")
print(f"Ring Distribution: {status['ring_distribution']}")
```

### Monitor Device Status

```python
# Access individual device status
for slave_id, device in master.device_statuses.items():
    print(f"{device.device_name}:")
    print(f"  Ring: {device.assigned_ring.value}")
    print(f"  Battery: {device.battery_level}%")
    print(f"  CPU: {device.cpu_usage:.1f}%")
    print(f"  Healthy: {device.is_healthy()}")
```

## Message Types

### New Message Types

- **RING_ASSIGNMENT**: Master → Slave, assigns a ring
- **DEVICE_STATUS_UPDATE**: Slave → Master, periodic device status update

### Ring Assignment Message

```python
{
    "message_type": "ring_assignment",
    "sender_id": "master-orchestrator",
    "receiver_id": "slave-001",
    "payload": {
        "ring": "prod",
        "reason": "Manual reassignment",
        "timestamp": "2025-10-16T12:34:56"
    }
}
```

### Device Status Update Message

```python
{
    "message_type": "device_status_update",
    "sender_id": "slave-001",
    "receiver_id": "master-orchestrator",
    "payload": {
        "device_status": {
            "slave_id": "slave-001",
            "battery_level": 85,
            "battery_charging": true,
            "cpu_usage": 45.2,
            "memory_usage": 62.5,
            "disk_usage": 55.0,
            "assigned_ring": "prod",
            "device_name": "Pixel 8 Pro",
            "os_version": "Android 14",
            "app_version": "1.0.0",
            "last_updated": "2025-10-16T12:34:56"
        }
    }
}
```

## Device Health Criteria

A device is considered **healthy** if:

- Battery level > 20%
- CPU usage < 80%
- Memory usage < 85%

Unhealthy devices are automatically moved to CANARY or DEV rings.

## Rebalancing Strategy

The rebalancer implements several strategies:

1. **Health-Based Movement**: Unhealthy devices removed from PROD
2. **Random Distribution**: 10% chance of random reassignment for load balancing
3. **Even Distribution**: New devices distributed evenly across rings
4. **Progressive Rollout**: Canary → Dev → Stage → Prod

## Configuration

### Rebalancing Interval

```python
# In orchestrator.py
async def _ring_rebalancer(self):
    while self.running:
        await asyncio.sleep(30)  # Check every 30 seconds
        # ... rebalancing logic
```

### Device Monitoring Interval

```python
# In agent.py
async def _monitor_device_status(self):
    while self.running:
        self.device_status.update_metrics()
        await asyncio.sleep(10)  # Update every 10 seconds
```

## Running the Example

```bash
# Navigate to aws-orchestrator directory
cd aws-orchestrator

# Install dependencies
pip install -r requirements.txt

# Run dynamic ring assignment example
python examples/dynamic_ring_assignment.py
```

## Expected Output

```
2025-10-16 12:34:56 - INFO - Starting Dynamic Ring Assignment Example
2025-10-16 12:34:56 - INFO - Creating master orchestrator...
2025-10-16 12:34:58 - INFO - Creating slave agents...
2025-10-16 12:34:59 - INFO - Slave registered: slave-001-1234 with capabilities: {...}
2025-10-16 12:34:59 - INFO - Assigned slave slave-001-1234 to ring dev: Auto-assignment
2025-10-16 12:35:10 - INFO - ========================================
2025-10-16 12:35:10 - INFO - CLUSTER STATUS UPDATE
2025-10-16 12:35:10 - INFO - Total Slaves: 8
2025-10-16 12:35:10 - INFO - Healthy Devices: 7
2025-10-16 12:35:10 - INFO - Ring Distribution:
2025-10-16 12:35:10 - INFO -   - canary: 2 devices
2025-10-16 12:35:10 - INFO -   - dev: 2 devices
2025-10-16 12:35:10 - INFO -   - stage: 2 devices
2025-10-16 12:35:10 - INFO -   - prod: 2 devices
```

## Best Practices

1. **Monitor Device Health**: Regularly check device status to identify problematic devices
2. **Gradual Rollouts**: Start with CANARY, validate, then progress to higher rings
3. **Health Thresholds**: Adjust health criteria based on your specific requirements
4. **Rebalancing Frequency**: Tune the rebalancing interval based on cluster size
5. **Manual Override**: Use manual ring assignment for critical updates or testing

## Advanced Features

### Custom Health Criteria

Modify `DeviceStatus.is_healthy()` to implement custom health checks:

```python
def is_healthy(self) -> bool:
    """Custom health criteria."""
    return (
        self.battery_level > 30 and  # Stricter battery requirement
        self.cpu_usage < 70 and       # Lower CPU threshold
        self.memory_usage < 80 and    # Lower memory threshold
        self.disk_usage < 90          # Add disk check
    )
```

### Ring-Specific Deployments

Target specific rings for deployments:

```python
# Deploy only to PROD ring
prod_slaves = master.ring_assignments[RingType.PROD]
for slave_id in prod_slaves:
    await master.submit_task(
        task_type="deployment",
        parameters={"version": "2.0.0", "target": slave_id}
    )
```

### Progressive Rollout Strategy

```python
async def progressive_rollout(master, version):
    """Progressive rollout across rings."""
    rings = [RingType.CANARY, RingType.DEV, RingType.STAGE, RingType.PROD]
    
    for ring in rings:
        print(f"Deploying to {ring.value}...")
        
        # Deploy to all slaves in ring
        slaves = master.ring_assignments[ring]
        for slave_id in slaves:
            await master.submit_task(
                task_type="deployment",
                parameters={"version": version, "ring": ring.value}
            )
        
        # Wait for validation before next ring
        await asyncio.sleep(60)  # Wait 1 minute
        print(f"{ring.value} deployment complete")
```

## Troubleshooting

### Issue: Devices not being assigned rings

**Solution**: Ensure device status is being sent during registration:
```python
await self._send_message(
    MessageType.REGISTRATION,
    {"capabilities": {...}, "device_status": self.device_status.to_dict()}
)
```

### Issue: Ring rebalancing too aggressive

**Solution**: Adjust the rebalancing interval or reduce random reassignment probability:
```python
# Change from 0.1 (10%) to 0.05 (5%)
elif random.random() < 0.05:
    # ... rebalancing logic
```

### Issue: All devices marked unhealthy

**Solution**: Adjust health thresholds in `DeviceStatus.is_healthy()` or fix metric simulation.

## Future Enhancements

- **Machine Learning**: Use AWS Strands to predict optimal ring assignments
- **Historical Analysis**: Track device performance over time
- **Custom Metrics**: Support additional device metrics (network, temperature, etc.)
- **Ring Policies**: Define custom policies for ring assignment rules
- **Rollback Support**: Automatic rollback on deployment failures
- **A/B Testing**: Support for split testing across rings

## Conclusion

The Dynamic Ring Assignment System provides intelligent, automated device management for progressive deployment strategies. It continuously monitors device health, balances load across rings, and ensures optimal resource utilization while maintaining system reliability.
