"""Ring assignment and management."""

import asyncio
import logging
from typing import Dict, List

from .config_loader import (
    DB_AVAILABLE, 
    get_ring_configurations, 
    update_device_ring
)
from ..common import RingType

logger = logging.getLogger(__name__)


class RingManager:
    """Manages device ring assignments."""
    
    def __init__(self, config, device_manager):
        self.config = config
        self.device_manager = device_manager
        self.ring_assignments: Dict[RingType, List[str]] = {ring: [] for ring in RingType}
        self.ring_configs: Dict[str, dict] = {}
        self.ring_rebalance_interval = 30.0
    
    async def load_ring_configurations(self):
        """Load ring configurations from database."""
        if DB_AVAILABLE:
            try:
                rings = get_ring_configurations()
                if rings:
                    self.ring_configs = {f"Ring {r['ring_id']}": r for r in rings}
                    logger.info(f"Loaded {len(self.ring_configs)} ring configurations")
                else:
                    logger.warning("No ring configurations found, using defaults")
                    self.ring_configs = self._get_default_configs()
            except Exception as e:
                logger.error(f"Error loading ring configurations: {e}")
                self.ring_configs = self._get_default_configs()
        else:
            logger.warning("Database not available, using default ring configurations")
            self.ring_configs = self._get_default_configs()
    
    def _get_default_configs(self) -> Dict[str, dict]:
        """Get default ring configurations."""
        return {
            f"Ring {i}": {
                "ring_id": i,
                "ring_name": f"Ring {i}",
                "categorization_prompt": f"Ring {i} devices"
            }
            for i in range(4)
        }
    
    async def auto_assign_ring(self, slave_id: str):
        """Auto-assign slave to optimal ring."""
        if slave_id not in self.device_manager.device_statuses:
            return
        
        optimal_ring = self._determine_optimal_ring(slave_id)
        await self.assign_to_ring(slave_id, optimal_ring, "Auto-assignment")
    
    async def assign_to_ring(self, slave_id: str, ring: RingType, reason: str = "Manual"):
        """Assign slave to a specific ring."""
        # Remove from old ring
        for r, devices in self.ring_assignments.items():
            if slave_id in devices:
                devices.remove(slave_id)
        
        # Add to new ring
        if ring not in self.ring_assignments:
            self.ring_assignments[ring] = []
        self.ring_assignments[ring].append(slave_id)
        
        # Update device status
        if slave_id in self.device_manager.device_statuses:
            self.device_manager.device_statuses[slave_id].assigned_ring = ring
        
        logger.info(f"Assigned {slave_id} to ring {ring.value}: {reason}")
        await self.update_ring_in_db(slave_id, ring)
    
    def _determine_optimal_ring(self, slave_id: str) -> RingType:
        """Determine optimal ring based on device metrics."""
        if slave_id not in self.device_manager.device_statuses:
            return RingType.DEV
        
        device_status = self.device_manager.device_statuses[slave_id]
        risk_score = self.device_manager.calculate_device_risk_score(device_status)
        
        # Ring assignment logic
        if risk_score >= 80 and device_status.cpu_usage <= 25.0:
            return RingType.PROD
        elif risk_score >= 50 and device_status.cpu_usage <= 60.0:
            return RingType.DEV
        elif risk_score >= 25:
            return RingType.STAGE
        else:
            return RingType.CANARY
    
    async def ring_rebalancer_loop(self, get_running_state):
        """Periodically rebalance ring assignments."""
        while True:
            is_running = get_running_state() if callable(get_running_state) else get_running_state
            if not is_running:
                break
                
            try:
                await asyncio.sleep(self.ring_rebalance_interval)
                logger.debug("Running ring rebalancing check")
            except Exception as e:
                logger.error(f"Error in ring rebalancer: {e}")
    
    async def update_ring_in_db(self, agent_id: str, ring: RingType):
        """Update device ring assignment in database."""
        if not DB_AVAILABLE:
            return
        
        # Get device_id from agent_id
        if agent_id.startswith("agent-"):
            device_id = agent_id[6:]
        else:
            device_id = None
            for cached_device in self.device_manager.device_cache.values():
                if f"agent-{cached_device['device_id']}" == agent_id:
                    device_id = cached_device["device_id"]
                    break
        
        if device_id:
            ring_to_id = {
                RingType.CANARY: 0,
                RingType.DEV: 1,
                RingType.STAGE: 2,
                RingType.PROD: 3,
                RingType.UNASSIGNED: 1
            }
            ring_id = ring_to_id.get(ring, 1)
            update_device_ring(device_id, ring_id)
