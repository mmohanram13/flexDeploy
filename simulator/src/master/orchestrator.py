"""Master orchestrator agent that coordinates slave agents."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from .device_manager import DeviceManager
from .deployment_manager import DeploymentManager
from .ring_manager import RingManager
from .agent_spawner import AgentSpawner
from ..common import (
    Message,
    MessageType,
    Task,
    TaskStatus,
    OrchestratorConfig,
    QueueManager,
)

logger = logging.getLogger(__name__)


class MasterOrchestrator:
    """Master agent that orchestrates and coordinates slave agents."""
    
    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self.agent_id = getattr(config, "master_id", "master-001")
        
        # Initialize queue manager
        try:
            qm_args = {}
            if hasattr(config, "message_queue_type"):
                qm_args["queue_type"] = config.message_queue_type
            if hasattr(config, "task_queue_size"):
                qm_args["maxsize"] = config.task_queue_size
            self.queue_manager = QueueManager(**qm_args) if qm_args else QueueManager()
        except Exception:
            self.queue_manager = QueueManager()

        # Initialize managers
        self.device_manager = DeviceManager(config)
        self.deployment_manager = DeploymentManager(config, self.device_manager)
        self.ring_manager = RingManager(config, self.device_manager)
        self.agent_spawner = AgentSpawner(config, self.queue_manager, self.device_manager)
        
        # State management
        self.slaves: Dict[str, dict] = {}
        self.tasks: Dict[str, Task] = {}
        self.task_queue: List[Task] = []
        
        # State flags
        self.running = False
        self._background_tasks: List[asyncio.Task] = []
        
        logger.info(f"Master orchestrator initialized: {self.agent_id}")
    
    async def start(self):
        """Start the master orchestrator."""
        if self.running:
            logger.warning("Master orchestrator already running")
            return
        
        self.running = True
        logger.info("Starting master orchestrator...")
        
        # Load data from database
        await self.device_manager.load_devices_from_db()
        await self.ring_manager.load_ring_configurations()
        
        # Start background tasks with lambda to get current running state
        self._background_tasks = [
            asyncio.create_task(self._heartbeat_monitor()),
            asyncio.create_task(self._task_monitor()),
            asyncio.create_task(self.ring_manager.ring_rebalancer_loop(lambda: self.running)),
            asyncio.create_task(self.deployment_manager.deployment_watcher_loop(lambda: self.running)),
            asyncio.create_task(self.device_manager.attribute_alteration_loop(lambda: self.running))
        ]
        
        # Start message processing
        await self._process_messages()
    
    async def stop(self):
        """Stop the master orchestrator."""
        logger.info("Stopping master orchestrator...")
        self.running = False
        
        # Cancel background tasks
        for task in self._background_tasks:
            if task and not task.done():
                task.cancel()
        
        # Notify all slaves
        await self._broadcast_shutdown()
        
        # Stop all agents
        await self.agent_spawner.stop_all_agents()
        
        logger.info("Master orchestrator stopped")
    
    async def register_slave(self, slave_id: str, capabilities: dict, device_status_dict: dict = None) -> bool:
        """Register a new slave agent."""
        if slave_id in self.slaves:
            logger.warning(f"Slave {slave_id} already registered")
            return False
        
        # Create device status and register
        device_status = self.device_manager.create_device_status(slave_id, capabilities, device_status_dict)
        
        self.slaves[slave_id] = {
            "slave_id": slave_id,
            "capabilities": capabilities,
            "status": "idle",
            "registered_at": datetime.now(),
            "last_heartbeat": datetime.now(),
            "assigned_tasks": [],
            "completed_tasks": 0,
            "failed_tasks": 0,
            "device_status": device_status.to_dict() if device_status else {}
        }
        
        logger.info(f"Slave registered: {slave_id}")
        
        # Auto-assign to ring
        await self.ring_manager.auto_assign_ring(slave_id)
        
        # Send acknowledgement
        await self._send_message(
            MessageType.ACK,
            slave_id,
            {"status": "registered", "message": "Welcome to the cluster"}
        )
        
        return True
    
    async def start_deployment(self, deployment_id: str) -> dict:
        """Start a deployment."""
        return await self.deployment_manager.start_deployment(
            deployment_id,
            self.agent_spawner.agents
        )
    
    async def complete_deployment(self, deployment_id: str) -> dict:
        """Complete a deployment."""
        return await self.deployment_manager.complete_deployment(deployment_id)
    
    def spawn_agent_random(self):
        """Spawn a random agent."""
        return self.agent_spawner.spawn_agent_random()
    
    async def on_asset_added(self, asset: dict):
        """Handle asset addition from UI."""
        return await self.agent_spawner.on_asset_added(asset)
    
    async def get_cluster_status(self) -> dict:
        """Get cluster status."""
        return self.device_manager.get_cluster_status(
            self.slaves,
            self.tasks,
            self.ring_manager.ring_assignments
        )
    
    async def _heartbeat_monitor(self):
        """Monitor slave heartbeats."""
        while self.running:
            try:
                await asyncio.sleep(self.config.slave_heartbeat_interval)
            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {e}")
    
    async def _task_monitor(self):
        """Monitor task progress."""
        while self.running:
            try:
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Error in task monitor: {e}")
    
    async def _process_messages(self):
        """Process incoming messages."""
        logger.info("Starting message processing loop")
        while self.running:
            try:
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    
    async def _send_message(self, message_type: MessageType, receiver_id: str, payload: dict):
        """Send a message to a slave."""
        message = Message(
            message_type=message_type,
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            timestamp=datetime.now(),
            payload=payload
        )
        await self.queue_manager.send_message(message)
    
    async def _broadcast_shutdown(self):
        """Broadcast shutdown to all slaves."""
        for slave_id in list(self.slaves.keys()):
            try:
                await self._send_message(MessageType.SHUTDOWN, slave_id, {"reason": "Master shutting down"})
            except Exception as e:
                logger.error(f"Error sending shutdown to {slave_id}: {e}")