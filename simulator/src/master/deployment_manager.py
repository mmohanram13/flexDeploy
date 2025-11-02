"""Deployment management and monitoring."""

import asyncio
import logging
import random
from datetime import datetime
from typing import Optional, Dict, List

from .config_loader import (
    DB_AVAILABLE,
    get_db_connection,
    update_device_attributes
)

logger = logging.getLogger(__name__)


class DeploymentManager:
    """Manages deployments and scenarios."""

    def __init__(self, config, device_manager):
        self.config = config
        self.device_manager = device_manager
        self.deployment_active = False
        self.deployment_id: Optional[str] = None
        self.deployment_start_time: Optional[datetime] = None
        self.deployment_monitor_interval = 3.0  # Check every 3 seconds
        
        # Track affected devices during deployment
        self.affected_devices: Dict[str, Dict] = {}  # agent_id -> original_metrics
        
        # Tracking processed deployments
        self.processed_deployments: set = set()
        self.last_check_time: Optional[datetime] = None
        
        # Ring progression tracking
        self.current_ring_index = 0
        self.ring_start_time: Optional[datetime] = None
        self.ring_completion_time = 20.0  # 20 seconds per ring
        
        # Batch device updates to reduce database contention
        self.pending_device_updates: Dict[str, Dict] = {}
        self.last_batch_update: Optional[datetime] = None
        self.batch_update_interval = 5.0  # Batch updates every 5 seconds

    async def start_deployment(self, deployment_id: str, agents: dict) -> dict:
        """Start a deployment."""
        self.deployment_active = True
        self.deployment_id = deployment_id
        self.deployment_start_time = datetime.now()
        self.affected_devices = {}
        self.current_ring_index = 0
        self.ring_start_time = datetime.now()

        logger.info(f"Deployment {deployment_id} started with {len(agents)} agents")

        # Update deployment status to In Progress
        if DB_AVAILABLE:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE deployments 
                    SET status = 'In Progress', updated_at = CURRENT_TIMESTAMP
                    WHERE deployment_id = ?
                """, (deployment_id,))
                
                # Set first ring to In Progress
                cursor.execute("""
                    UPDATE deployment_rings 
                    SET status = 'In Progress', updated_at = CURRENT_TIMESTAMP
                    WHERE deployment_id = ? AND ring_id = 0
                """, (deployment_id,))
                
                conn.commit()
                conn.close()
                logger.info(f"Deployment {deployment_id} status updated to In Progress")
            except Exception as e:
                logger.error(f"Error updating deployment status: {e}")

        # Simulate deployment impact on devices
        await self._simulate_deployment_impact(agents)

        return {
            "deployment_id": deployment_id,
            "status": "active",
            "agent_count": len(agents),
            "affected_devices": len(self.affected_devices),
            "start_time": self.deployment_start_time.isoformat()
        }

    async def complete_deployment(self, deployment_id: str) -> dict:
        """Complete a deployment."""
        logger.info(f"Completing deployment {deployment_id}")

        # Flush any pending updates first
        await self._flush_pending_device_updates()
        
        # Update device statuses in database with final values
        await self._finalize_device_updates()

        # Update deployment status in database
        if DB_AVAILABLE:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Use a single transaction for both updates
                cursor.execute("""
                    UPDATE deployments 
                    SET status = 'Completed', updated_at = CURRENT_TIMESTAMP
                    WHERE deployment_id = ?
                """, (deployment_id,))

                cursor.execute("""
                    UPDATE deployment_rings 
                    SET status = 'Completed', updated_at = CURRENT_TIMESTAMP
                    WHERE deployment_id = ? AND status != 'Failed'
                """, (deployment_id,))

                conn.commit()
                conn.close()
                logger.info(f"Deployment {deployment_id} marked as completed in database")
            except Exception as e:
                logger.error(f"Error updating deployment status: {e}")

        self.deployment_active = False
        self.affected_devices = {}
        self.pending_device_updates = {}

        return {
            "deployment_id": deployment_id,
            "status": "completed",
            "completion_time": datetime.now().isoformat()
        }

    async def _simulate_deployment_impact(self, agents: dict):
        """Simulate deployment impact on device metrics."""
        if not agents:
            logger.warning("No agents to affect during deployment")
            return

        # Select 40-70% of agents for deployment impact
        impact_percentage = random.uniform(0.4, 0.7)
        num_affected = max(1, int(len(agents) * impact_percentage))
        affected_agent_ids = random.sample(list(agents.keys()), min(num_affected, len(agents)))

        logger.info(f"Simulating deployment impact on {len(affected_agent_ids)} devices")

        for agent_id in affected_agent_ids:
            if agent_id in self.device_manager.device_statuses:
                device_status = self.device_manager.device_statuses[agent_id]

                # Store original metrics
                self.affected_devices[agent_id] = {
                    "original_cpu": device_status.cpu_usage,
                    "original_memory": device_status.memory_usage,
                    "original_disk": device_status.disk_usage,
                    "original_battery": device_status.battery_level
                }

                # Apply deployment impact (increased resource usage)
                cpu_increase = random.uniform(15.0, 40.0)
                memory_increase = random.uniform(10.0, 30.0)
                disk_increase = random.uniform(5.0, 15.0)

                device_status.cpu_usage = min(95.0, device_status.cpu_usage + cpu_increase)
                device_status.memory_usage = min(90.0, device_status.memory_usage + memory_increase)
                device_status.disk_usage = min(90.0, device_status.disk_usage + disk_increase)

                # Battery drain if not charging
                if not device_status.battery_charging:
                    battery_drain = random.uniform(5.0, 15.0)
                    device_status.battery_level = max(5.0, device_status.battery_level - battery_drain)

                device_status.last_updated = datetime.now()

                logger.debug(
                    f"Device {agent_id} impacted - "
                    f"CPU: {self.affected_devices[agent_id]['original_cpu']:.1f}% → {device_status.cpu_usage:.1f}%, "
                    f"Memory: {self.affected_devices[agent_id]['original_memory']:.1f}% → {device_status.memory_usage:.1f}%"
                )

    async def _finalize_device_updates(self):
        """Finalize device updates after deployment completion."""
        if not self.affected_devices:
            return

        logger.info(f"Finalizing device updates for {len(self.affected_devices)} devices")

        # Batch all updates together
        updates_to_process = []

        for agent_id, original_metrics in self.affected_devices.items():
            if agent_id in self.device_manager.device_statuses:
                device_status = self.device_manager.device_statuses[agent_id]

                # Apply post-deployment adjustments
                # Some devices recover, others maintain higher usage
                recovery_factor = random.uniform(0.3, 0.7)

                original_cpu = original_metrics["original_cpu"]
                original_memory = original_metrics["original_memory"]

                # Partial recovery from deployment spike
                device_status.cpu_usage = original_cpu + (device_status.cpu_usage - original_cpu) * recovery_factor
                device_status.memory_usage = original_memory + (device_status.memory_usage - original_memory) * recovery_factor

                # Update in device manager
                device_status.last_updated = datetime.now()

                # Calculate new risk score
                risk_score = self.device_manager.calculate_device_risk_score(device_status)

                # Get device_id from agent_id
                device_id = None
                if agent_id.startswith("agent-"):
                    device_id = agent_id[6:]
                else:
                    for cached_device in self.device_manager.device_cache.values():
                        if f"agent-{cached_device['device_id']}" == agent_id:
                            device_id = cached_device["device_id"]
                            break

                if device_id:
                    risk_score = self.device_manager.calculate_device_risk_score(device_status)
                    updates_to_process.append({
                        'device_id': device_id,
                        'cpu': device_status.cpu_usage,
                        'memory': device_status.memory_usage,
                        'disk': device_status.disk_usage,
                        'risk': risk_score
                    })

        # Process all updates in a single transaction
        if DB_AVAILABLE and updates_to_process:
            await self._batch_update_devices(updates_to_process)

        logger.info("Device updates finalized in database")

    async def _batch_update_devices(self, updates: List[Dict]):
        """Update multiple devices in a single transaction."""
        if not updates:
            return
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            for update in updates:
                cursor.execute("""
                    UPDATE devices 
                    SET avg_cpu_usage = ?, 
                        avg_memory_usage = ?, 
                        avg_disk_space = ?, 
                        risk_score = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE device_id = ?
                """, (update['cpu'], update['memory'], update['disk'], update['risk'], update['device_id']))
            
            conn.commit()
            conn.close()
            logger.debug(f"Batch updated {len(updates)} devices in database")
        except Exception as e:
            logger.error(f"Error in batch device update: {e}")

    async def deployment_watcher_loop(self, get_running_state):
        """Watch for deployment changes and monitor progress."""
        logger.info("Starting deployment watcher loop")

        while True:
            # Check if orchestrator is still running
            is_running = get_running_state() if callable(get_running_state) else get_running_state
            if not is_running:
                break
                
            try:
                # Check for new or updated deployments
                await self._check_deployment_table()

                # Monitor active deployment progress
                if self.deployment_active and self.deployment_id:
                    await self._monitor_deployment_progress()

                await asyncio.sleep(self.deployment_monitor_interval)
            except Exception as e:
                logger.error(f"Error in deployment watcher: {e}")
                await asyncio.sleep(self.deployment_monitor_interval)

        logger.info("Deployment watcher loop stopped")

    async def _check_deployment_table(self):
        """Check deployment table for new or updated deployments."""
        if not DB_AVAILABLE:
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Get deployments with status 'Not Started' to auto-start
            deployments = cursor.execute("""
                SELECT deployment_id, deployment_name, status, created_at, updated_at
                FROM deployments
                WHERE status = 'Not Started' OR (status = 'In Progress' AND deployment_id = ?)
                ORDER BY created_at DESC
            """, (self.deployment_id if self.deployment_id else '',)).fetchall()

            for deployment in deployments:
                dep_id = deployment["deployment_id"]
                dep_name = deployment["deployment_name"]
                status = deployment["status"]

                if dep_id not in self.processed_deployments and status == 'Not Started':
                    logger.info(f"New deployment detected: {dep_id} - {dep_name}")
                    self.processed_deployments.add(dep_id)
                    
                    # Auto-start the deployment
                    logger.info(f"Auto-starting deployment: {dep_id}")
                    # Get agents from device manager
                    from ..slave.agent import SlaveAgent
                    agents = {aid: agent for aid, agent in self.device_manager.device_statuses.items()}
                    await self.start_deployment(dep_id, agents)

            conn.close()

        except Exception as e:
            logger.error(f"Error checking deployment table: {e}")

    async def _monitor_deployment_progress(self):
        """Monitor progress of active deployment."""
        if not self.deployment_id or not DB_AVAILABLE:
            return

        try:
            # Periodically update device metrics during deployment
            await self._update_device_metrics_during_deployment()
            
            # Flush pending updates periodically
            await self._check_and_flush_updates()
            
            # Progress through rings
            await self._progress_rings()

        except Exception as e:
            logger.error(f"Error monitoring deployment progress: {e}")

    async def _check_and_flush_updates(self):
        """Check if it's time to flush pending device updates."""
        if not self.last_batch_update:
            self.last_batch_update = datetime.now()
            return
        
        elapsed = (datetime.now() - self.last_batch_update).total_seconds()
        if elapsed >= self.batch_update_interval:
            await self._flush_pending_device_updates()
            self.last_batch_update = datetime.now()

    async def _flush_pending_device_updates(self):
        """Flush all pending device updates to database."""
        if not self.pending_device_updates:
            return
        
        updates = list(self.pending_device_updates.values())
        self.pending_device_updates = {}
        
        await self._batch_update_devices(updates)

    async def _update_device_metrics_during_deployment(self):
        """Update device metrics during active deployment."""
        if not self.affected_devices:
            return

        # Randomly fluctuate metrics for affected devices
        for agent_id in list(self.affected_devices.keys()):
            if agent_id in self.device_manager.device_statuses:
                device_status = self.device_manager.device_statuses[agent_id]

                # Random fluctuation during deployment
                cpu_change = random.uniform(-5.0, 10.0)
                memory_change = random.uniform(-3.0, 8.0)

                device_status.cpu_usage = max(10.0, min(95.0, device_status.cpu_usage + cpu_change))
                device_status.memory_usage = max(20.0, min(90.0, device_status.memory_usage + memory_change))
                device_status.last_updated = datetime.now()

    async def _progress_rings(self):
        """Progress through deployment rings automatically."""
        if not DB_AVAILABLE or not self.ring_start_time:
            return

        elapsed = (datetime.now() - self.ring_start_time).total_seconds()
        
        # Check if current ring should be completed
        if elapsed >= self.ring_completion_time:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                # Get all rings for this deployment
                rings = cursor.execute("""
                    SELECT ring_id, ring_name, status
                    FROM deployment_rings
                    WHERE deployment_id = ?
                    ORDER BY ring_id
                """, (self.deployment_id,)).fetchall()
                
                # Complete current ring
                if self.current_ring_index < len(rings):
                    current_ring = rings[self.current_ring_index]
                    
                    cursor.execute("""
                        UPDATE deployment_rings 
                        SET status = 'Completed', updated_at = CURRENT_TIMESTAMP
                        WHERE deployment_id = ? AND ring_id = ?
                    """, (self.deployment_id, current_ring["ring_id"]))
                    
                    logger.info(f"Ring {current_ring['ring_name']} completed")
                    
                    # Update device metrics for completed ring
                    await self._update_ring_devices_in_db(current_ring["ring_id"])
                    
                    # Move to next ring
                    self.current_ring_index += 1
                    
                    if self.current_ring_index < len(rings):
                        # Start next ring
                        next_ring = rings[self.current_ring_index]
                        cursor.execute("""
                            UPDATE deployment_rings 
                            SET status = 'In Progress', updated_at = CURRENT_TIMESTAMP
                            WHERE deployment_id = ? AND ring_id = ?
                        """, (self.deployment_id, next_ring["ring_id"]))
                        
                        self.ring_start_time = datetime.now()
                        logger.info(f"Ring {next_ring['ring_name']} started")
                        
                        # Apply impacts to new ring devices
                        await self._apply_ring_specific_impacts(next_ring["ring_id"])
                    else:
                        # All rings completed - finalize deployment
                        logger.info("All rings completed, finalizing deployment")
                        await self.complete_deployment(self.deployment_id)
                
                conn.commit()
                conn.close()
                
            except Exception as e:
                logger.error(f"Error progressing rings: {e}")

    async def _update_ring_devices_in_db(self, ring_id: int):
        """Update all devices in a ring with current metrics."""
        logger.info(f"Queueing devices in Ring {ring_id} for batch update")
        
        for agent_id, device_status in self.device_manager.device_statuses.items():
            # Check if device is in this ring
            if hasattr(device_status.assigned_ring, 'value'):
                ring_value = device_status.assigned_ring.value
                # Extract ring number from value (e.g., "ring-1" -> 1)
                if ring_value.startswith('ring-'):
                    device_ring_id = int(ring_value.split('-')[1])
                else:
                    device_ring_id = -1
            else:
                device_ring_id = -1
            
            if device_ring_id == ring_id:
                # Calculate risk score
                risk_score = self.device_manager.calculate_device_risk_score(device_status)
                
                # Get device_id from agent_id
                device_id = None
                if agent_id.startswith("agent-"):
                    device_id = agent_id[6:]
                else:
                    for cached_device in self.device_manager.device_cache.values():
                        if f"agent-{cached_device['device_id']}" == agent_id:
                            device_id = cached_device["device_id"]
                            break
                
                if device_id:
                    # Queue for batch update instead of immediate update
                    self.pending_device_updates[device_id] = {
                        'device_id': device_id,
                        'cpu': device_status.cpu_usage,
                        'memory': device_status.memory_usage,
                        'disk': device_status.disk_usage,
                        'risk': risk_score
                    }
        
        # Flush the batch
        await self._flush_pending_device_updates()

    async def _apply_ring_specific_impacts(self, ring_id: int):
        """Apply specific impacts to devices in a ring during deployment."""
        logger.info(f"Applying deployment impacts to Ring {ring_id}")

        # Find devices in this ring
        for agent_id, device_status in self.device_manager.device_statuses.items():
            if device_status.assigned_ring.value == f"ring-{ring_id}":
                # Add to affected devices if not already
                if agent_id not in self.affected_devices:
                    self.affected_devices[agent_id] = {
                        "original_cpu": device_status.cpu_usage,
                        "original_memory": device_status.memory_usage,
                        "original_disk": device_status.disk_usage,
                        "original_battery": device_status.battery_level
                    }

                # Apply deployment impact
                device_status.cpu_usage = min(95.0, device_status.cpu_usage + random.uniform(10.0, 25.0))
                device_status.memory_usage = min(90.0, device_status.memory_usage + random.uniform(8.0, 20.0))
                device_status.last_updated = datetime.now()

    async def get_deployment_details(self, deployment_id: str) -> Optional[Dict]:
        """Get detailed deployment information."""
        if not DB_AVAILABLE:
            return None

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            deployment = cursor.execute("""
                SELECT deployment_id, deployment_name, status, created_at, updated_at
                FROM deployments
                WHERE deployment_id = ?
            """, (deployment_id,)).fetchone()

            if not deployment:
                conn.close()
                return None

            rings = cursor.execute("""
                SELECT ring_id, ring_name, device_count, status, failure_reason
                FROM deployment_rings
                WHERE deployment_id = ?
                ORDER BY ring_id
            """, (deployment_id,)).fetchall()

            conn.close()

            return {
                "deployment_id": deployment["deployment_id"],
                "deployment_name": deployment["deployment_name"],
                "status": deployment["status"],
                "created_at": deployment["created_at"],
                "updated_at": deployment["updated_at"],
                "rings": [
                    {
                        "ring_id": ring["ring_id"],
                        "ring_name": ring["ring_name"],
                        "device_count": ring["device_count"],
                        "status": ring["status"],
                        "failure_reason": ring["failure_reason"]
                    }
                    for ring in rings
                ]
            }
        except Exception as e:
            logger.error(f"Error getting deployment details: {e}")
            return None
