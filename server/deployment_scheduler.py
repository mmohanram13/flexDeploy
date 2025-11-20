"""
Deployment Scheduler Service
Manages automatic deployment progression through rings with gating factor checks.
"""
import asyncio
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DeploymentScheduler:
    """
    Manages automatic deployment progression through rings.
    Checks gating factors every 30 seconds and progresses to next ring if checks pass.
    """
    
    def __init__(self, db_connection: sqlite3.Connection, simulator_service):
        self.conn = db_connection
        self.simulator_service = simulator_service
        self.active_deployments: Dict[str, asyncio.Task] = {}
        self.deployment_timers: Dict[str, Dict] = {}  # Track timing info
    
    async def start_deployment(self, deployment_id: str):
        """
        Start automated deployment progression for a deployment.
        
        Args:
            deployment_id: The deployment ID to start
        """
        # Cancel existing task if running
        if deployment_id in self.active_deployments:
            self.active_deployments[deployment_id].cancel()
            try:
                await self.active_deployments[deployment_id]
            except asyncio.CancelledError:
                pass
        
        # Start new deployment task
        task = asyncio.create_task(self._run_deployment(deployment_id))
        self.active_deployments[deployment_id] = task
        
        # Initialize timer info
        self.deployment_timers[deployment_id] = {
            'startTime': datetime.now().isoformat(),
            'currentRing': 0,
            'nextCheckTime': None,
            'status': 'running'
        }
        
        logger.info(f"Started deployment scheduler for {deployment_id}")
    
    async def stop_deployment(self, deployment_id: str):
        """
        Stop automated deployment progression for a deployment.
        
        Args:
            deployment_id: The deployment ID to stop
        """
        if deployment_id in self.active_deployments:
            self.active_deployments[deployment_id].cancel()
            try:
                await self.active_deployments[deployment_id]
            except asyncio.CancelledError:
                pass
            
            del self.active_deployments[deployment_id]
            
            if deployment_id in self.deployment_timers:
                self.deployment_timers[deployment_id]['status'] = 'stopped'
            
            logger.info(f"Stopped deployment scheduler for {deployment_id}")
    
    def get_deployment_timer_info(self, deployment_id: str) -> Optional[Dict]:
        """
        Get timer information for a deployment.
        
        Returns:
            Dict with timing information or None if not found
        """
        return self.deployment_timers.get(deployment_id)
    
    async def _run_deployment(self, deployment_id: str):
        """
        Main deployment progression loop.
        Progresses through rings 0-3, checking gating factors every 30 seconds.
        """
        try:
            cursor = self.conn.cursor()
            
            # Get all rings for this deployment (should be 0, 1, 2, 3)
            rings = cursor.execute("""
                SELECT ring_id, ring_name, status
                FROM deployment_rings
                WHERE deployment_id = ?
                ORDER BY ring_id
            """, (deployment_id,)).fetchall()
            
            if not rings:
                logger.error(f"No rings found for deployment {deployment_id}")
                return
            
            # Process each ring sequentially
            for ring_id, ring_name, current_status in rings:
                # Skip if ring is already completed or failed
                if current_status in ['Completed', 'Failed']:
                    continue
                
                logger.info(f"Processing Ring {ring_id} ({ring_name}) for deployment {deployment_id}")
                
                # Check if ring has any devices
                device_count = cursor.execute("""
                    SELECT COUNT(*)
                    FROM devices
                    WHERE ring = ?
                """, (ring_id,)).fetchone()[0]
                
                if device_count == 0:
                    # No devices in ring - automatically mark as completed
                    logger.info(f"Ring {ring_id} has no devices, marking as Completed")
                    cursor.execute("""
                        UPDATE deployment_rings
                        SET status = 'Completed',
                            updated_at = CURRENT_TIMESTAMP
                        WHERE deployment_id = ? AND ring_id = ?
                    """, (deployment_id, ring_id))
                    self.conn.commit()
                    continue
                
                # Update timer info
                self.deployment_timers[deployment_id]['currentRing'] = ring_id
                next_check = datetime.now() + timedelta(seconds=30)
                self.deployment_timers[deployment_id]['nextCheckTime'] = next_check.isoformat()
                
                # Mark ring as In Progress
                cursor.execute("""
                    UPDATE deployment_rings
                    SET status = 'In Progress',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE deployment_id = ? AND ring_id = ?
                """, (deployment_id, ring_id))
                self.conn.commit()
                
                logger.info(f"Ring {ring_id} marked as In Progress, waiting 30 seconds...")
                
                # Wait 30 seconds for deployment to settle
                await asyncio.sleep(30)
                
                # Check gating factors
                logger.info(f"Checking gating factors for Ring {ring_id}...")
                gating_check = self.simulator_service.check_gating_factors(
                    deployment_id=deployment_id,
                    ring_id=ring_id
                )
                
                if gating_check["status"] == "failed":
                    # Gating factors breached - deployment failed
                    logger.error(f"Gating factors breached for Ring {ring_id}: {gating_check['failureReason']}")
                    
                    # The check_gating_factors method already:
                    # 1. Marks the ring as Failed
                    # 2. Stops all other rings
                    # 3. Marks deployment as Failed
                    
                    # Update timer info
                    self.deployment_timers[deployment_id]['status'] = 'failed'
                    self.deployment_timers[deployment_id]['nextCheckTime'] = None
                    
                    # Stop processing
                    break
                
                # Gating factors passed - mark ring as Completed
                logger.info(f"Ring {ring_id} passed gating factor checks, marking as Completed")
                cursor.execute("""
                    UPDATE deployment_rings
                    SET status = 'Completed',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE deployment_id = ? AND ring_id = ?
                """, (deployment_id, ring_id))
                self.conn.commit()
            
            # Check if all rings completed successfully
            completed_rings = cursor.execute("""
                SELECT COUNT(*)
                FROM deployment_rings
                WHERE deployment_id = ? AND status = 'Completed'
            """, (deployment_id,)).fetchone()[0]
            
            total_rings = len(rings)
            
            if completed_rings == total_rings:
                # All rings completed - mark deployment as Completed
                logger.info(f"All rings completed for deployment {deployment_id}, marking deployment as Completed")
                cursor.execute("""
                    UPDATE deployments
                    SET status = 'Completed',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE deployment_id = ?
                """, (deployment_id,))
                self.conn.commit()
                
                # Update timer info
                self.deployment_timers[deployment_id]['status'] = 'completed'
                self.deployment_timers[deployment_id]['nextCheckTime'] = None
            
            # Clean up
            if deployment_id in self.active_deployments:
                del self.active_deployments[deployment_id]
            
            logger.info(f"Deployment scheduler completed for {deployment_id}")
            
        except asyncio.CancelledError:
            logger.info(f"Deployment scheduler cancelled for {deployment_id}")
            raise
        except Exception as e:
            logger.error(f"Error in deployment scheduler for {deployment_id}: {str(e)}")
            
            # Mark deployment as failed
            try:
                cursor = self.conn.cursor()
                cursor.execute("""
                    UPDATE deployments
                    SET status = 'Failed',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE deployment_id = ?
                """, (deployment_id,))
                self.conn.commit()
                
                # Update timer info
                if deployment_id in self.deployment_timers:
                    self.deployment_timers[deployment_id]['status'] = 'error'
                    self.deployment_timers[deployment_id]['error'] = str(e)
            except:
                pass
