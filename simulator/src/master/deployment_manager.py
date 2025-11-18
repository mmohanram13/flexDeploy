"""Deployment management and monitoring."""

import asyncio
import logging
import random
from datetime import datetime
from typing import Optional, Dict, List

from .config_loader import (
    DB_AVAILABLE,
    get_db_connection,
    update_device_attributes,
    update_deployment_status,
    update_ring_status
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
        self.affected_devices: Dict[str, Dict] = {}
        
        # Tracking processed deployments
        self.processed_deployments: set = set()
        self.last_check_time: Optional[datetime] = None
        
        # Ring progression tracking
        self.current_ring_index = 0
        self.ring_start_time: Optional[datetime] = None
        self.ring_completion_time = 20.0  # 20 seconds per ring
        
        # Batch device updates
        self.pending_device_updates: Dict[str, Dict] = {}
        self.last_batch_update: Optional[datetime] = None
        self.batch_update_interval = 5.0
        
        # Watcher tracking metrics
        self.watcher_stats = {
            "total_loops": 0,
            "deployments_detected": 0,
            "deployments_started": 0,
            "deployments_completed": 0,
            "rings_completed": 0,
            "device_updates_flushed": 0,
            "errors": 0
        }

    async def start_deployment(self, deployment_id: str, agents: dict) -> dict:
        """Start a deployment."""
        self.deployment_active = True
        self.deployment_id = deployment_id
        self.deployment_start_time = datetime.now()
        self.affected_devices = {}
        self.current_ring_index = 0
        self.ring_start_time = datetime.now()

        logger.info(f"Deployment {deployment_id} started with {len(agents)} agents")

        # Update deployment status to In Progress using async function
        if DB_AVAILABLE:
            try:
                logger.info(f"Updating deployment {deployment_id} status to 'In Progress'...")
                success = await update_deployment_status(deployment_id, 'In Progress')
                if success:
                    logger.info(f"[OK] Deployment {deployment_id} status updated to In Progress")
                else:
                    logger.error(f"[WARN] Failed to update deployment status via async function, trying direct update...")
                    # Fallback to direct update
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE deployments 
                        SET status = 'In Progress', updated_at = CURRENT_TIMESTAMP
                        WHERE deployment_id = ?
                    """, (deployment_id,))
                    conn.commit()
                    conn.close()
                    logger.info(f"[OK] Deployment {deployment_id} status updated to In Progress (direct)")
                
                # Set first ring to In Progress
                logger.info(f"Updating Ring 0 status to 'In Progress'...")
                success = await update_ring_status(deployment_id, 0, 'In Progress')
                if success:
                    logger.info(f"[OK] Ring 0 status updated to In Progress")
                else:
                    logger.error(f"[WARN] Failed to update ring status via async function, trying direct update...")
                    # Fallback to direct update
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE deployment_rings 
                        SET status = 'In Progress', updated_at = CURRENT_TIMESTAMP
                        WHERE deployment_id = ? AND ring_id = 0
                    """, (deployment_id,))
                    conn.commit()
                    conn.close()
                    logger.info(f"[OK] Ring 0 status updated to In Progress (direct)")
                
            except Exception as e:
                logger.error(f"Error updating deployment status: {e}")
                import traceback
                logger.error(traceback.format_exc())

        # Verify the update was successful by reading back the status
        if DB_AVAILABLE:
            try:
                logger.info("Verifying deployment status update...")
                conn = get_db_connection()
                cursor = conn.cursor()
                result = cursor.execute("""
                    SELECT status FROM deployments WHERE deployment_id = ?
                """, (deployment_id,)).fetchone()
                conn.close()
                
                if result:
                    logger.info(f"[VERIFY] Deployment {deployment_id} current status in DB: {result['status']}")
                    if result['status'] != 'In Progress':
                        logger.error(f"[ERROR] Status verification failed! Expected 'In Progress', got '{result['status']}'")
                else:
                    logger.error(f"[ERROR] Could not verify deployment status - deployment not found!")
            except Exception as e:
                logger.error(f"[ERROR] Status verification failed: {e}")

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
        logger.info("=" * 80)
        logger.info(f"[COMPLETING DEPLOYMENT] {deployment_id}")
        logger.info("=" * 80)

        # Flush any pending updates first
        try:
            logger.info("Step 1: Flushing pending device updates...")
            await self._flush_pending_device_updates()
            logger.info("[OK] Flushed pending device updates")
        except Exception as e:
            logger.error(f"[ERROR] flushing pending updates: {e}")
        
        # Update device statuses in database with final values
        try:
            logger.info("Step 2: Finalizing device updates...")
            await self._finalize_device_updates()
            logger.info("[OK] Finalized device updates")
        except Exception as e:
            logger.error(f"[ERROR] finalizing device updates: {e}")

        # Reassign devices to rings based on updated metrics (except Ring 3 - VIP)
        try:
            logger.info("Step 2.5: Reassigning devices to rings based on updated metrics...")
            await self._reassign_devices_to_rings()
            logger.info("[OK] Ring reassignment completed")
        except Exception as e:
            logger.error(f"[ERROR] reassigning devices to rings: {e}")

        # Update deployment status using the async-safe function
        if DB_AVAILABLE:
            logger.info(f"Step 3: Updating deployment {deployment_id} status to Completed...")
            success = await update_deployment_status(deployment_id, 'Completed')
            if success:
                logger.info(f"[OK] Deployment {deployment_id} marked as COMPLETED in database")
            else:
                logger.error(f"[ERROR] Failed to update deployment {deployment_id} status")
                # Try direct database update as fallback
                try:
                    logger.info("Attempting direct database update as fallback...")
                    conn = get_db_connection()
                    cursor = conn.cursor()
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
                    logger.info("[OK] Direct database update successful")
                except Exception as e2:
                    logger.error(f"[ERROR] Direct database update also failed: {e2}")
        else:
            logger.error("[ERROR] DB_AVAILABLE is False, cannot update deployment status")

        # Reset deployment state
        logger.info("Step 4: Resetting deployment state...")
        self.deployment_active = False
        self.affected_devices = {}
        self.pending_device_updates = {}
        
        # Remove from processed set to allow re-running
        if deployment_id in self.processed_deployments:
            self.processed_deployments.remove(deployment_id)
            logger.info(f"[OK] Removed {deployment_id} from processed set - can be run again")
        
        logger.info("[OK] Deployment state reset")

        logger.info("=" * 80)
        logger.info(f"[DEPLOYMENT FINISHED] {deployment_id}")
        logger.info("=" * 80)

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

    async def _reassign_devices_to_rings(self):
        """Reassign devices to rings based on updated metrics after deployment.
        Ring 3 (VIP) devices remain unchanged.
        Other rings are reassigned based on risk scores and randomization.
        """
        if not DB_AVAILABLE:
            logger.warning("Cannot reassign rings: DB not available")
            return
        
        logger.info("=" * 80)
        logger.info("RING REASSIGNMENT - Starting reassignment based on updated metrics")
        logger.info("=" * 80)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get all devices except Ring 3 (VIP devices stay in Ring 3)
            devices = cursor.execute("""
                SELECT device_id, device_name, ring, avg_cpu_usage, avg_memory_usage, 
                       avg_disk_space, risk_score
                FROM devices
                WHERE ring != 3
                ORDER BY device_id
            """).fetchall()
            
            logger.info(f"Found {len(devices)} devices eligible for ring reassignment (excluding Ring 3)")
            
            reassignment_count = 0
            ring_changes = {0: 0, 1: 0, 2: 0}  # Track changes per ring
            
            for device in devices:
                old_ring = device['ring']
                device_id = device['device_id']
                risk_score = device['risk_score']
                avg_cpu = device['avg_cpu_usage']
                avg_memory = device['avg_memory_usage']
                avg_disk_space = device['avg_disk_space']
                
                # Calculate new ring based on risk score and metrics with some randomization
                new_ring = self._calculate_ring_assignment(
                    risk_score, avg_cpu, avg_memory, avg_disk_space, old_ring
                )
                
                if new_ring != old_ring:
                    # Update device ring in database
                    cursor.execute("""
                        UPDATE devices 
                        SET ring = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE device_id = ?
                    """, (new_ring, device_id))
                    
                    # Update in device manager if the device is being tracked
                    agent_id = f"agent-{device_id}"
                    if agent_id in self.device_manager.device_statuses:
                        device_status = self.device_manager.device_statuses[agent_id]
                        from ..common import RingType
                        device_status.assigned_ring = RingType(f"ring-{new_ring}")
                    
                    reassignment_count += 1
                    ring_changes[new_ring] = ring_changes.get(new_ring, 0) + 1
                    
                    logger.info(
                        f"[REASSIGN] {device['device_name']} ({device_id}): "
                        f"Ring {old_ring} → Ring {new_ring} "
                        f"(Risk: {risk_score}, CPU: {avg_cpu:.1f}%, Mem: {avg_memory:.1f}%)"
                    )
            
            conn.commit()
            conn.close()
            
            logger.info("=" * 80)
            logger.info(f"[RING REASSIGNMENT COMPLETE]")
            logger.info(f"Total devices reassigned: {reassignment_count} / {len(devices)}")
            logger.info(f"New Ring 0 assignments: {ring_changes.get(0, 0)}")
            logger.info(f"New Ring 1 assignments: {ring_changes.get(1, 0)}")
            logger.info(f"New Ring 2 assignments: {ring_changes.get(2, 0)}")
            logger.info(f"Ring 3 (VIP): No changes (protected)")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Error during ring reassignment: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def _calculate_ring_assignment(self, risk_score: int, cpu_usage: float, 
                                   memory_usage: float, disk_space: float, 
                                   current_ring: int) -> int:
        """Calculate ring assignment based on device metrics with randomization.
        
        Ring assignment logic:
        - Ring 0 (Canary): Test devices, low risk devices with stable metrics
        - Ring 1 (Low Risk): Devices with high risk scores (71-100)
        - Ring 2 (High Risk): Devices with medium risk scores (31-70)
        - Ring 3 (VIP): Not reassigned (handled by caller)
        
        Adds randomization to prevent deterministic assignments.
        """
        # Calculate average resource usage
        avg_usage = (cpu_usage + memory_usage + (100 - disk_space)) / 3.0
        
        # Base ring determination on risk score
        if risk_score >= 71:
            # High risk score (low resource usage) - candidates for Ring 1 or Ring 0
            base_ring = 1
            # 20% chance to move to Ring 0 (Canary)
            if random.random() < 0.20:
                base_ring = 0
        elif risk_score >= 31:
            # Medium risk score (moderate resource usage) - Ring 2
            base_ring = 2
            # 15% chance to move to Ring 1 if on the higher end
            if risk_score >= 60 and random.random() < 0.15:
                base_ring = 1
        else:
            # Low risk score (high resource usage) - Ring 2
            base_ring = 2
        
        # Add some stability - 30% chance to keep current ring if it's close
        if current_ring in [0, 1, 2]:
            ring_diff = abs(base_ring - current_ring)
            if ring_diff <= 1 and random.random() < 0.30:
                return current_ring
        
        # Additional randomization: 10% chance to shift by one ring (within bounds)
        if random.random() < 0.10:
            shift = random.choice([-1, 1])
            candidate_ring = base_ring + shift
            if 0 <= candidate_ring <= 2:
                base_ring = candidate_ring
        
        return base_ring

    async def deployment_watcher_loop(self, get_running_state):
        """Deployment watcher with detailed execution tracking."""
        logger.info("=" * 80)
        logger.info("DEPLOYMENT WATCHER LOOP - ENTRY POINT REACHED")
        logger.info("=" * 80)
        
        try:
            # Test async/await is working
            logger.info("TEST 1: Testing async sleep...")
            await asyncio.sleep(0.1)
            logger.info("TEST 1: [OK] Async sleep works")
            
            # Test get_running_state
            logger.info("TEST 2: Testing get_running_state...")
            test_running = get_running_state() if callable(get_running_state) else get_running_state
            logger.info(f"TEST 2: [OK] Running state = {test_running}")
            
            # Test DB connection
            logger.info(f"TEST 3: DB_AVAILABLE = {DB_AVAILABLE}")
            
            if DB_AVAILABLE:
                logger.info("TEST 3: Testing database connection...")
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM deployments")
                    count = cursor.fetchone()[0]
                    conn.close()
                    logger.info(f"TEST 3: [OK] Database accessible, {count} deployments found")
                except Exception as e:
                    logger.error(f"TEST 3: [ERROR] Database error: {e}")
            
            logger.info("=" * 80)
            logger.info("ALL PRE-FLIGHT CHECKS PASSED - STARTING MAIN LOOP")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"PRE-FLIGHT CHECK FAILED: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return
        
        loop_count = 0
        last_status_log = datetime.now()

        while True:
            loop_count += 1
            self.watcher_stats["total_loops"] = loop_count
            
            logger.info("=" * 80)
            logger.info(f"LOOP {loop_count} START - {datetime.now().isoformat()}")
            logger.info("=" * 80)
            
            # Check running state
            try:
                logger.info(f"[{loop_count}] Step 1: Checking running state...")
                is_running = get_running_state() if callable(get_running_state) else get_running_state
                logger.info(f"[{loop_count}] Step 1: [OK] Running = {is_running}")
                
                if not is_running:
                    logger.info("Orchestrator stopped, exiting watcher loop")
                    break
            except Exception as e:
                logger.error(f"[{loop_count}] Step 1: [ERROR] {e}")
            
            # Check deployment table
            try:
                logger.info(f"[{loop_count}] Step 2: About to call _check_deployment_table()...")
                logger.info(f"[{loop_count}] Step 2: Method exists: {hasattr(self, '_check_deployment_table')}")
                logger.info(f"[{loop_count}] Step 2: Method callable: {callable(getattr(self, '_check_deployment_table', None))}")
                
                await self._check_deployment_table()
                
                logger.info(f"[{loop_count}] Step 2: [OK] _check_deployment_table() completed")
            except Exception as e:
                logger.error(f"[{loop_count}] Step 2: [ERROR] {e}")
                import traceback
                logger.error(traceback.format_exc())
            
            # Monitor deployment progress
            try:
                logger.info(f"[{loop_count}] Step 3: Checking active deployment...")
                if self.deployment_active and self.deployment_id:
                    logger.info(f"[{loop_count}] Step 3: Active deployment: {self.deployment_id}")
                    await self._monitor_deployment_progress()
                    logger.info(f"[{loop_count}] Step 3: [OK] Monitoring completed")
                else:
                    logger.info(f"[{loop_count}] Step 3: No active deployment")
            except Exception as e:
                logger.error(f"[{loop_count}] Step 3: [ERROR] {e}")
                import traceback
                logger.error(traceback.format_exc())
            
            # Sleep
            try:
                logger.info(f"[{loop_count}] Step 4: Sleeping for {self.deployment_monitor_interval}s...")
                await asyncio.sleep(self.deployment_monitor_interval)
                logger.info(f"[{loop_count}] Step 4: [OK] Sleep completed")
            except Exception as e:
                logger.error(f"[{loop_count}] Step 4: [ERROR] {e}")
            
            logger.info("=" * 80)
            logger.info(f"LOOP {loop_count} END")
            logger.info("=" * 80)

        logger.info("DEPLOYMENT WATCHER STOPPED")

    async def _check_deployment_table(self):
        """Check deployment table with detailed logging."""
        logger.info(">>> _check_deployment_table() ENTERED <<<")
        
        logger.info(f"DB_AVAILABLE check: {DB_AVAILABLE}")
        
        if not DB_AVAILABLE:
            logger.warning("[ERROR] DB_AVAILABLE is False")
            return
        
        logger.info("[OK] DB_AVAILABLE is True, proceeding...")
        
        try:
            logger.info("Connecting to database...")
            conn = get_db_connection()
            logger.info("[OK] Database connection obtained")
            
            cursor = conn.cursor()
            logger.info("[OK] Cursor created")
            
            logger.info("Executing query...")
            deployments = cursor.execute("""
                SELECT deployment_id, deployment_name, status
                FROM deployments
                WHERE status = 'Started'
                ORDER BY created_at DESC
            """).fetchall()
            
            logger.info(f"[OK] Query executed, found {len(deployments)} deployments with status='Started'")
            logger.info(f"[INFO] Currently processed deployments: {self.processed_deployments}")
            
            for i, deployment in enumerate(deployments):
                logger.info(f"  [{i}] {deployment['deployment_id']}: {deployment['deployment_name']} ({deployment['status']})")
                
                if deployment["deployment_id"] not in self.processed_deployments:
                    logger.info(f"  [{i}] NEW - will start deployment")
                    self.processed_deployments.add(deployment["deployment_id"])
                    
                    agents = {aid: agent for aid, agent in self.device_manager.device_statuses.items()}
                    logger.info(f"  [{i}] Starting with {len(agents)} agents...")
                    
                    await self.start_deployment(deployment["deployment_id"], agents)
                    
                    logger.info(f"  [{i}] [OK] Deployment started")
                    logger.info(f"  [{i}] Updated processed_deployments: {self.processed_deployments}")
                else:
                    logger.warning(f"  [{i}] SKIP - {deployment['deployment_id']} already in processed_deployments set")
                    logger.warning(f"  [{i}] This deployment will not be picked up again until it completes")
            
            if len(deployments) == 0:
                logger.info("[INFO] No deployments found with status='Started'")
            
            conn.close()
            logger.info("[OK] Database connection closed")
            
        except Exception as e:
            logger.error(f"[ERROR] in _check_deployment_table: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        logger.info("<<< _check_deployment_table() EXITING >>>")

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

    async def _check_and_flush_updates(self):
        """Check if it's time to flush pending device updates."""
        if not self.last_batch_update:
            self.last_batch_update = datetime.now()
            return
        
        elapsed = (datetime.now() - self.last_batch_update).total_seconds()
        if elapsed >= self.batch_update_interval:
            updates_count = len(self.pending_device_updates)
            if updates_count > 0:
                logger.info(f"Flushing {updates_count} pending device updates to database")
            await self._flush_pending_device_updates()
            self.watcher_stats["device_updates_flushed"] += updates_count
            self.last_batch_update = datetime.now()

    async def _flush_pending_device_updates(self):
        """Flush all pending device updates to database."""
        if not self.pending_device_updates:
            return
        
        updates = list(self.pending_device_updates.values())
        self.pending_device_updates = {}
        
        await self._batch_update_devices(updates)

    async def _progress_rings(self):
        """Progress through rings and complete deployment."""
        if not DB_AVAILABLE or not self.ring_start_time:
            logger.debug("Cannot progress rings: DB_AVAILABLE={DB_AVAILABLE}, ring_start_time={self.ring_start_time}")
            return

        elapsed = (datetime.now() - self.ring_start_time).total_seconds()
        
        logger.debug(f"Ring progress check: elapsed={elapsed:.1f}s, required={self.ring_completion_time}s, current_ring_index={self.current_ring_index}")
        
        if elapsed >= self.ring_completion_time:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                
                rings = cursor.execute("""
                    SELECT ring_id, ring_name, status
                    FROM deployment_rings
                    WHERE deployment_id = ?
                    ORDER BY ring_id
                """, (self.deployment_id,)).fetchall()
                
                conn.close()
                
                logger.info(f"Deployment {self.deployment_id}: Total rings={len(rings)}, Current index={self.current_ring_index}")
                
                if self.current_ring_index < len(rings):
                    current_ring = rings[self.current_ring_index]
                    
                    logger.info("=" * 80)
                    logger.info(f"[RING COMPLETE] Ring {current_ring['ring_id']}: {current_ring['ring_name']}")
                    logger.info(f"Elapsed time: {elapsed:.1f}s")
                    logger.info("=" * 80)
                    
                    # Mark current ring as completed
                    await update_ring_status(self.deployment_id, current_ring["ring_id"], 'Completed')
                    self.watcher_stats["rings_completed"] += 1
                    logger.info(f"[OK] Ring {current_ring['ring_name']} marked as Completed")
                    
                    # Update devices in this ring
                    logger.info(f"Updating devices in Ring {current_ring['ring_id']}...")
                    await self._update_ring_devices_in_db(current_ring["ring_id"])
                    logger.info(f"[OK] Devices updated for Ring {current_ring['ring_id']}")
                    
                    # Move to next ring
                    self.current_ring_index += 1
                    logger.info(f"Moved to ring index: {self.current_ring_index}")
                    
                    # Check if there are more rings
                    if self.current_ring_index < len(rings):
                        # Start next ring
                        next_ring = rings[self.current_ring_index]
                        
                        logger.info("=" * 80)
                        logger.info(f"[RING START] Ring {next_ring['ring_id']}: {next_ring['ring_name']}")
                        logger.info("=" * 80)
                        
                        await update_ring_status(self.deployment_id, next_ring["ring_id"], 'In Progress')
                        self.ring_start_time = datetime.now()
                        logger.info(f"[OK] Ring {next_ring['ring_name']} marked as In Progress at {self.ring_start_time}")
                        
                        # Apply impacts to new ring devices
                        logger.info(f"Applying impacts to Ring {next_ring['ring_id']} devices...")
                        await self._apply_ring_specific_impacts(next_ring["ring_id"])
                        logger.info(f"[OK] Impacts applied to Ring {next_ring['ring_id']}")
                    else:
                        # ALL RINGS COMPLETED - Finalize deployment
                        logger.info("=" * 80)
                        logger.info(f"[DEPLOYMENT COMPLETE] ALL {len(rings)} RINGS COMPLETED")
                        logger.info(f"Deployment ID: {self.deployment_id}")
                        logger.info(f"Total time: {(datetime.now() - self.deployment_start_time).total_seconds():.1f}s")
                        logger.info("=" * 80)
                        
                        logger.info("Calling complete_deployment()...")
                        result = await self.complete_deployment(self.deployment_id)
                        self.watcher_stats["deployments_completed"] += 1
                        
                        logger.info(f"[OK] Deployment completed: {result}")
                        logger.info("=" * 80)
                else:
                    logger.warning(f"Ring index {self.current_ring_index} out of bounds (total rings: {len(rings)})")
                
            except Exception as e:
                logger.error(f"[ERROR] in _progress_rings: {e}")
                import traceback
                logger.error(traceback.format_exc())

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
