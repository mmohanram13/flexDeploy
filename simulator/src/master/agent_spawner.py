"""Agent spawning and lifecycle management."""

import asyncio
import logging
import random
import uuid
from typing import Dict

from .config_loader import DB_AVAILABLE, get_device_by_id
from ..common import RingType
from ..slave.agent import SlaveAgent

logger = logging.getLogger(__name__)


class AgentSpawner:
    """Manages agent spawning and lifecycle."""
    
    def __init__(self, config, queue_manager, device_manager):
        self.config = config
        self.queue_manager = queue_manager
        self.device_manager = device_manager
        self.agents: Dict[str, SlaveAgent] = {}
        self._agent_tasks: Dict[str, asyncio.Task] = {}
        self.agent_to_asset: Dict[str, dict] = {}
    
    def spawn_agent_from_device(self, device_dict: dict) -> str:
        """Spawn agent from device configuration."""
        slave_id = f"agent-{device_dict['device_id']}"
        capabilities = {
            "device_id": device_dict["device_id"],
            "name": device_dict["device_name"],
            "manufacturer": device_dict["manufacturer"],
            "model": device_dict["model"],
            "osName": device_dict["os_name"],
            "battery": random.randint(40, 95),
            "cpu": device_dict["avg_cpu_usage"] / 100.0
        }
        
        agent = SlaveAgent(
            slave_id=slave_id,
            master_id="master-001",
            capabilities=capabilities,
            config=self.config,
            queue_manager=self.queue_manager
        )
        
        self.agents[slave_id] = agent
        task = agent.start_in_background()
        self._agent_tasks[slave_id] = task
        
        # Create device status
        self.device_manager.create_device_status(slave_id, capabilities)
        self.agent_to_asset[slave_id] = device_dict
        
        logger.info(f"Spawned agent {slave_id}")
        return slave_id
    
    def spawn_agent_random(self):
        """Spawn a random agent."""
        if not self.device_manager.device_cache:
            devices = self.device_manager._get_fallback_devices()
            self.device_manager.device_cache = {d["device_id"]: d for d in devices}
        
        if self.device_manager.device_cache:
            device_dict = random.choice(list(self.device_manager.device_cache.values()))
            return self.spawn_agent_from_device(device_dict)
        
        return None
    
    async def on_asset_added(self, asset: dict):
        """Handle asset addition."""
        logger.info(f"Asset added: {asset}")
        
        matching_device = None
        if DB_AVAILABLE and "device_id" in asset:
            try:
                matching_device = get_device_by_id(asset["device_id"])
            except Exception as e:
                logger.error(f"Error fetching device: {e}")
        
        if matching_device:
            agent_id = self.spawn_agent_from_device(matching_device)
        else:
            agent_id = self.spawn_agent_random()
        
        if agent_id:
            self.agent_to_asset[agent_id] = asset
        
        return agent_id
    
    async def stop_all_agents(self):
        """Stop all spawned agents."""
        for agent_id, task in list(self._agent_tasks.items()):
            try:
                if not task.done():
                    task.cancel()
                    await asyncio.wait([task], timeout=1.0)
                logger.info(f"Stopped agent {agent_id}")
            except Exception as e:
                logger.error(f"Error stopping agent {agent_id}: {e}")
        
        self.agents.clear()
        self._agent_tasks.clear()
