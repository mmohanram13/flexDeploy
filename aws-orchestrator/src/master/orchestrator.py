"""Master orchestrator agent that coordinates slave agents."""

import asyncio
from doctest import master
import logging
import uuid
import random
from datetime import datetime
from typing import Dict, List, Optional, Any

# Guard optional Strands import (may not be installed in demo env)
try:
    from strands import Agent
except Exception:
    Agent = None

from ..common import (
    Message,
    MessageType,
    Task,
    TaskStatus,
    DeviceStatus,
    RingType,
    OrchestratorConfig,
    QueueManager,
)
from ..common.config import OrchestratorConfig
from ..common.queue import QueueManager
from ..slave.agent import SlaveAgent


logger = logging.getLogger(__name__)


class MasterOrchestrator:
    """Master agent that orchestrates and coordinates slave agents."""
    
    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self.agent_id = getattr(config, "master_id", "master-001")

        # Robust QueueManager construction: try using config attrs, fallback to default init
        try:
            qm_args = {}
            if hasattr(config, "message_queue_type"):
                qm_args["queue_type"] = config.message_queue_type
            if hasattr(config, "task_queue_size"):
                qm_args["maxsize"] = config.task_queue_size
            self.queue_manager = QueueManager(**qm_args) if qm_args else QueueManager()
        except Exception:
            # final fallback - default constructor
            self.queue_manager = QueueManager()

        self.agents: Dict[str, SlaveAgent] = {}
        self._agent_tasks: Dict[str, asyncio.Task] = {}

        # State management
        self.slaves: Dict[str, dict] = {}  # slave_id -> slave_info
        self.device_statuses: Dict[str, DeviceStatus] = {}  # slave_id -> device_status
        self.tasks: Dict[str, Task] = {}  # task_id -> task
        self.task_queue: List[Task] = []  # Pending tasks
        self.ring_assignments: Dict[RingType, List[str]] = {
            ring: [] for ring in RingType
        }  # ring -> list of slave_ids
        
        # AWS Strands agent for AI capabilities
        self.strands_agent: Optional[Agent] = None
        
        # Add explicit logging about Strands initialization
        use_strands = getattr(config, "use_aws_strands", False)
        print(f"[Master] AWS Strands integration enabled: {use_strands}")
        
        if use_strands:
            try:
                self._initialize_strands_agent()
                print(f"[Master] Strands agent initialized successfully: {self.strands_agent is not None}")
            except Exception as e:
                print(f"[Master] Failed to initialize Strands agent: {e}")
        
        # State flags
        self.running = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._task_monitor_task: Optional[asyncio.Task] = None
        self._ring_rebalancer_task: Optional[asyncio.Task] = None
        
        # Deployment tracking
        self.deployment_active = False
        self.deployment_id: Optional[str] = None
        self.deployment_start_time: Optional[datetime] = None
        
        # Asset tracking - map agent ID to asset details
        self.agent_to_asset: Dict[str, Dict[str, Any]] = {}
        
        # subscribe to heartbeat topic for demo
        self.queue_manager.subscribe("heartbeat", self._handle_heartbeat)

        logger.info(f"Master orchestrator initialized: {self.agent_id}")
    
    def _initialize_strands_agent(self):
        """Initialize AWS Strands agent for AI capabilities."""
        if Agent is None:
            print("[Master] WARNING: Strands package not imported successfully.")
            print("[Master] Make sure you have installed it with: pip install aws-strands")
            logger.warning("Strands package not available; skipping Strands agent initialization")
            self.strands_agent = None
            return

        try:
            # Try minimal parameters first to see if we can get it working
            model = getattr(self.config, "strands_model", "amazon.nova-act-v1:0")
            print(f"[Master] Initializing Strands agent with model: {model}")
            
            # Fallback to absolute minimal initialization
            self.strands_agent = Agent(model=model)
            
            # After creating, try to set properties if needed
            if hasattr(self.strands_agent, 'name'):
                self.strands_agent.name = "master-orchestrator"
                
            print(f"[Master] Strands agent created successfully: {self.strands_agent}")
            logger.info("AWS Strands agent initialized")
        except Exception as e:
            # Print full traceback for better debugging
            import traceback
            print(f"[Master] Strands initialization error: {e}")
            print(traceback.format_exc())
            logger.error(f"Failed to initialize Strands agent: {e}")
            self.strands_agent = None
    
    async def start(self):
        """Start the master orchestrator."""
        if self.running:
            logger.warning("Master orchestrator already running")
            return
        
        self.running = True
        logger.info("Starting master orchestrator...")
        
        # Start background tasks
        self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
        self._task_monitor_task = asyncio.create_task(self._task_monitor())
        self._ring_rebalancer_task = asyncio.create_task(self._ring_rebalancer())
        
        # Start message processing
        await self._process_messages()
    
    async def stop(self):
        """Stop the master orchestrator."""
        logger.info("Stopping master orchestrator...")
        self.running = False
        
        # Cancel background tasks
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._task_monitor_task:
            self._task_monitor_task.cancel()
        if self._ring_rebalancer_task:
            self._ring_rebalancer_task.cancel()
        
        # Notify all slaves
        await self._broadcast_shutdown()
        
        logger.info("Master orchestrator stopped")
    
    async def register_slave(self, slave_id: str, capabilities: dict, device_status_dict: dict = None) -> bool:
        """Register a new slave agent."""
        if slave_id in self.slaves:
            logger.warning(f"Slave {slave_id} already registered")
            return False
        
        # Create device status from capabilities if not explicitly provided
        if not device_status_dict:
            battery_level = capabilities.get("battery", random.randint(40, 95))
            cpu_usage = capabilities.get("cpu", random.uniform(5.0, 25.0)) * 10  # Scale to percentage
            
            device_status_dict = {
                "slave_id": slave_id,
                "battery_level": battery_level,
                "battery_charging": random.choice([True, False]),
                "cpu_usage": cpu_usage,
                "memory_usage": random.uniform(20.0, 50.0),
                "disk_usage": random.uniform(30.0, 70.0),
                "device_name": capabilities.get("name", f"Agent-{slave_id[-6:]}"),
                "os_version": capabilities.get("osName", "Unknown"),
                "last_updated": datetime.now().isoformat()
            }
        
        # Parse device status
        if device_status_dict:
            try:
                device_status = DeviceStatus.from_dict(device_status_dict)
                self.device_statuses[slave_id] = device_status
            except Exception as e:
                logger.error(f"Failed to parse device status: {e}")
                # Create a default device status
                device_status = DeviceStatus(
                    slave_id=slave_id,
                    battery_level=capabilities.get("battery", 75),
                    battery_charging=random.choice([True, False]),
                    cpu_usage=capabilities.get("cpu", 10.0) * 10,  # Scale to percentage
                    memory_usage=random.uniform(20.0, 50.0),
                    disk_usage=random.uniform(30.0, 70.0),
                    device_name=f"Agent-{slave_id[-6:]}"  # Fixed: Added missing closing quote
                )
                self.device_statuses[slave_id] = device_status
                device_status_dict = device_status.to_dict()
        
        # Create slave entry
        self.slaves[slave_id] = {
            "slave_id": slave_id,
            "capabilities": capabilities,
            "status": "idle",
            "registered_at": datetime.now(),
            "last_heartbeat": datetime.now(),
            "assigned_tasks": [],
            "completed_tasks": 0,
            "failed_tasks": 0,
            "device_status": device_status_dict
        }
        
        logger.info(
            f"Slave registered: {slave_id} with capabilities: {capabilities}, "
            f"Device: {self.device_statuses[slave_id].device_name if slave_id in self.device_statuses else 'Unknown'}"
        )
        
        # Auto-assign to a ring based on device health
        await self._auto_assign_ring(slave_id)
        
        # Send acknowledgement
        await self._send_message(
            MessageType.ACK,
            slave_id,
            {"status": "registered", "message": "Welcome to the cluster"}
        )
        
        return True
    
    async def submit_task(self, task_type: str, parameters: dict, priority: int = 0) -> str:
        """Submit a new task for execution."""
        task_id = str(uuid.uuid4())
        task = Task(
            task_id=task_id,
            task_type=task_type,
            parameters=parameters,
            priority=priority,
            created_at=datetime.now()
        )
        
        self.tasks[task_id] = task
        self.task_queue.append(task)
        self.task_queue.sort(key=lambda t: t.priority, reverse=True)
        
        logger.info(f"Task submitted: {task_id} (type: {task_type}, priority: {priority})")
        
        # Try to assign immediately
        await self._assign_tasks()
        
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """Get the status of a task."""
        task = self.tasks.get(task_id)
        if not task:
            return None
        return task.to_dict()
    
    async def get_cluster_status(self) -> dict:
        """Get the overall cluster status."""
        total_tasks = len(self.tasks)
        pending_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING])
        in_progress_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS])
        completed_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED])
        failed_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED])
        
        # Count slaves by ring
        ring_distribution = {}
        for ring in RingType:
            ring_distribution[ring.value] = len(self.ring_assignments.get(ring, []))
        
        # Get device health stats
        healthy_devices = len([d for d in self.device_statuses.values() if d.is_healthy()])
        
        return {
            "master_id": self.agent_id,
            "running": self.running,
            "total_slaves": len(self.slaves),
            "active_slaves": len([s for s in self.slaves.values() if s["status"] == "busy"]),
            "idle_slaves": len([s for s in self.slaves.values() if s["status"] == "idle"]),
            "healthy_devices": healthy_devices,
            "total_tasks": total_tasks,
            "pending_tasks": pending_tasks,
            "in_progress_tasks": in_progress_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "ring_distribution": ring_distribution,
            "queue_stats": self.queue_manager.get_all_stats()
        }
    
    async def start_deployment(self, deployment_id: str) -> dict:
        """Mark deployment as active and trigger random agent metric changes."""
        self.deployment_active = True
        self.deployment_id = deployment_id
        self.deployment_start_time = datetime.now()
        logger.info(f"Deployment {deployment_id} started")
        
        # Ensure all agents have device status
        self._ensure_all_agents_have_device_status()
        
        # Simulate deployment activity affecting agent metrics
        affected_agents = await self._simulate_deployment_activity()
        
        logger.info(f"Deployment {deployment_id} started, affected {len(affected_agents)} agents")
        return {
            "deployment_id": deployment_id, 
            "status": "active",
            "affected_agents": affected_agents,
            "agent_count": len(self.agents)
        }
    
    def _ensure_all_agents_have_device_status(self):
        """Ensure all agents have device status objects for metric tracking."""
        for agent_id in list(self.agents.keys()):
            if agent_id not in self.device_statuses:
                print(f"Creating device status for agent {agent_id}")
                
                # Get capabilities if agent is registered
                capabilities = {}
                if agent_id in self.slaves:
                    capabilities = self.slaves[agent_id].get("capabilities", {})
                elif hasattr(self.agents[agent_id], "capabilities"):
                    capabilities = self.agents[agent_id].capabilities
                
                # Use capabilities for initial values if available
                battery = capabilities.get("battery", random.randint(40, 95))
                cpu = capabilities.get("cpu", random.uniform(5.0, 25.0))
                if cpu < 5:  # If CPU is a decimal (like 0.86), scale it to percentage
                    cpu *= 10
                
                # Create device status with appropriate values
                device_status = DeviceStatus(
                    slave_id=agent_id,
                    battery_level=battery,
                    battery_charging=random.choice([True, False]),
                    cpu_usage=cpu,
                    memory_usage=random.uniform(20.0, 50.0),
                    disk_usage=random.uniform(30.0, 70.0),
                    device_name=f"Agent-{agent_id[-6:]}",
                    os_version="Unknown"
                )
                self.device_statuses[agent_id] = device_status
                
                # If agent is in slaves dict but no device status, add it there too
                if agent_id in self.slaves:
                    self.slaves[agent_id]["device_status"] = device_status.to_dict()

    async def start_deployment(self, deployment_id: str) -> dict:
        """Mark deployment as active and trigger random agent metric changes."""
        self.deployment_active = True
        self.deployment_id = deployment_id
        self.deployment_start_time = datetime.now()
        logger.info(f"Deployment {deployment_id} started")
        
        # Ensure all agents have device status
        self._ensure_all_agents_have_device_status()
        
        # Simulate deployment activity affecting agent metrics
        affected_agents = await self._simulate_deployment_activity()
        
        logger.info(f"Deployment {deployment_id} started, affected {len(affected_agents)} agents")
        return {
            "deployment_id": deployment_id, 
            "status": "active",
            "affected_agents": affected_agents,
            "agent_count": len(self.agents)
        }
    
    async def _simulate_deployment_activity(self):
        """Simulate deployment affecting agent metrics (CPU, battery) randomly."""
        # Ensure all agents have device status objects for metric tracking
        self._ensure_all_agents_have_device_status()
        
        # Select random agents (30-50% of them) to simulate metric changes
        affected_agent_count = max(1, int(len(self.agents) * random.uniform(0.3, 0.5)))
        affected_agents = random.sample(list(self.agents.keys()), 
                                       min(affected_agent_count, len(self.agents)))
        
        print(f"Simulating deployment impact on {len(affected_agents)}/{len(self.agents)} agents")
        
        # Apply random changes to selected agents
        for agent_id in affected_agents:
            if agent_id in self.device_statuses:
                device_status = self.device_statuses[agent_id]
                
                # Store original values for logging
                orig_cpu = device_status.cpu_usage
                orig_battery = device_status.battery_level
                
                # Simulate CPU spike (10-50% increase)
                cpu_spike = random.uniform(10.0, 50.0)
                device_status.cpu_usage = min(95.0, device_status.cpu_usage + cpu_spike)
                
                # Simulate battery drain (5-15% decrease if not charging)
                if not device_status.battery_charging:
                    battery_drain = random.uniform(5.0, 15.0)
                    device_status.battery_level = max(5.0, device_status.battery_level - battery_drain)
                
                # Simulate memory increase (10-30%)
                memory_increase = random.uniform(10.0, 30.0)
                device_status.memory_usage = min(90.0, device_status.memory_usage + memory_increase)
                
                # Update last_updated timestamp
                device_status.last_updated = datetime.now()
                
                # Log the changes with before/after values
                print(f"Agent {agent_id} metrics changed - CPU: {orig_cpu:.1f}% → {device_status.cpu_usage:.1f}%, "
                      f"Battery: {orig_battery:.1f}% → {device_status.battery_level:.1f}%, "
                      f"Memory: {device_status.memory_usage:.1f}%")
                
                # Make sure changes are stored in slaves dict if agent is there
                if agent_id in self.slaves:
                    self.slaves[agent_id]["device_status"] = device_status.to_dict()
                
                # Update capabilities to match - this ensures consistency
                if agent_id in self.slaves:
                    self.slaves[agent_id]["capabilities"]["battery"] = int(device_status.battery_level)
                    self.slaves[agent_id]["capabilities"]["cpu"] = round(device_status.cpu_usage / 10, 2)
                
                # Update agent's capabilities directly if possible
                if agent_id in self.agents and hasattr(self.agents[agent_id], "capabilities"):
                    self.agents[agent_id].capabilities["battery"] = int(device_status.battery_level)
                    self.agents[agent_id].capabilities["cpu"] = round(device_status.cpu_usage / 10, 2)
        
        return affected_agents

    async def get_deployment_status(self, deployment_id: str = None) -> dict:
        """Get detailed deployment status with all agent information including full asset details."""
        if deployment_id is None:
            deployment_id = self.deployment_id or "current"
        
        agents_status = []
        
        # First add all registered slaves
        for slave_id, slave_info in self.slaves.items():
            device_status = self.device_statuses.get(slave_id)
            
            agent_detail = {
                "slave_id": slave_id,
                "status": slave_info.get("status", "unknown"),
                "capabilities": slave_info.get("capabilities", {}),
                "registered_at": slave_info.get("registered_at", "").isoformat() if hasattr(slave_info.get("registered_at", ""), "isoformat") else str(slave_info.get("registered_at")),
                "last_heartbeat": slave_info.get("last_heartbeat", "").isoformat() if hasattr(slave_info.get("last_heartbeat", ""), "isoformat") else str(slave_info.get("last_heartbeat")),
                "assigned_tasks": slave_info.get("assigned_tasks", []),
                "completed_tasks": slave_info.get("completed_tasks", 0),
                "failed_tasks": slave_info.get("failed_tasks", 0),
                "device_info": None,
                "ring_assignment": None,
                "asset": self.agent_to_asset.get(slave_id)  # Include full asset data
            }
            
            if device_status:
                agent_detail["device_info"] = {
                    "name": device_status.device_name,
                    "battery_level": device_status.battery_level,
                    "battery_charging": device_status.battery_charging,
                    "cpu_usage": device_status.cpu_usage,
                    "memory_usage": device_status.memory_usage,
                    "disk_usage": device_status.disk_usage,
                    "os_version": device_status.os_version,
                    "is_healthy": device_status.is_healthy()
                }
                agent_detail["ring_assignment"] = device_status.assigned_ring.value
            elif slave_info.get("device_status"):
                # If there's device_status in slave_info but not in self.device_statuses
                try:
                    ds = slave_info["device_status"]
                    agent_detail["device_info"] = {
                        "name": ds.get("device_name", f"Agent-{slave_id[-6:]}"),
                        "battery_level": ds.get("battery_level", 0),
                        "battery_charging": ds.get("battery_charging", False),
                        "cpu_usage": ds.get("cpu_usage", 0),
                        "memory_usage": ds.get("memory_usage", 0),
                        "disk_usage": ds.get("disk_usage", 0),
                        "os_version": ds.get("os_version", "Unknown"),
                        "is_healthy": True  # Assume healthy for now
                    }
                except Exception as e:
                    logger.error(f"Error parsing device status from slave_info: {e}")
            
            agents_status.append(agent_detail)
        
        # Now add any agents from self.agents that aren't in self.slaves yet
        for agent_id, agent in self.agents.items():
            if agent_id not in self.slaves:
                # Add a simpler status for agents that haven't fully registered
                agent_detail = {
                    "slave_id": agent_id,
                    "status": "spawned",  # Special status for spawned but not fully registered
                    "capabilities": getattr(agent, "capabilities", {}),
                    "registered_at": datetime.now().isoformat(),  # Just use current time
                    "last_heartbeat": datetime.now().isoformat(),  # Just use current time
                    "assigned_tasks": [],
                    "completed_tasks": 0,
                    "failed_tasks": 0,
                    "device_info": {
                        "name": f"Agent-{agent_id[-6:]}",  # Use shortened agent ID
                        "battery_level": None,
                        "cpu_usage": None,
                        "memory_usage": None,
                        "is_healthy": True  # Assume healthy initially
                    },
                    "ring_assignment": "unassigned",
                    "asset": self.agent_to_asset.get(agent_id)  # Include full asset data
                }
                agents_status.append(agent_detail)
        
        # Calculate active/idle agents including those from self.agents
        active_agents = len([s for s in self.slaves.values() if s["status"] == "busy"])
        idle_agents = len([s for s in self.slaves.values() if s["status"] == "idle"])
        # Add the agents that aren't in self.slaves yet (from self.agents)
        spawned_not_registered = len([aid for aid in self.agents.keys() if aid not in self.slaves])
        idle_agents += spawned_not_registered  # Consider them idle initially
        
        # Add a comprehensive asset list with their agent IDs
        assets = []
        for agent_id, asset in self.agent_to_asset.items():
            if asset:  # Some agents might not have an associated asset
                asset_status = {
                    "agent_id": agent_id,
                    "asset_data": asset,
                    "agent_status": "unknown"
                }
                
                # Add agent status if available
                if agent_id in self.slaves:
                    asset_status["agent_status"] = self.slaves[agent_id].get("status", "unknown")
                elif agent_id in self.agents:
                    asset_status["agent_status"] = "spawned"
                
                assets.append(asset_status)
        
        return {
            "deployment_id": deployment_id,
            "status": "active" if self.deployment_active else "completed",
            "start_time": self.deployment_start_time.isoformat() if self.deployment_start_time else None,
            "total_agents": len(self.slaves) + spawned_not_registered,  # Include all agents
            "active_agents": active_agents,
            "idle_agents": idle_agents,
            "healthy_devices": len([d for d in self.device_statuses.values() if d.is_healthy()]),
            "agents": agents_status,
            "assets": assets,  # Add comprehensive asset list
            "ring_distribution": {ring.value: len(self.ring_assignments.get(ring, [])) for ring in RingType},
            "spawned_agents": list(self.agents.keys()),  # Add this for debugging
            "registered_slaves": list(self.slaves.keys())  # Add this for debugging
        }
    
    async def complete_deployment(self, deployment_id: str) -> dict:
        """Mark deployment as complete and return all agent statuses."""
        if self.deployment_id != deployment_id:
            logger.warning(f"Deployment ID mismatch: {deployment_id}")
            return {"error": "deployment_id mismatch"}
        
        self.deployment_active = False
        deployment_duration = (datetime.now() - self.deployment_start_time).total_seconds() if self.deployment_start_time else 0
        
        # Simulate recovery of some agents after deployment completes
        recovered_agents = await self._simulate_agent_recovery()
        
        logger.info(f"Deployment {deployment_id} completed in {deployment_duration}s, recovered {len(recovered_agents)} agents")
        
        # Return full deployment status with all agent details
        result = await self.get_deployment_status(deployment_id)
        # Add recovery info
        result["recovered_agents"] = recovered_agents
        return result
    
    async def _simulate_agent_recovery(self):
        """Simulate some agents recovering to normal metrics after deployment."""
        # Select some agents to recover (40-80% of them)
        recovery_agent_count = max(1, int(len(self.agents) * random.uniform(0.4, 0.8)))
        recovery_agents = random.sample(list(self.agents.keys()), 
                                       min(recovery_agent_count, len(self.agents)))
        
        print(f"Simulating recovery for {len(recovery_agents)}/{len(self.agents)} agents")
        
        for agent_id in recovery_agents:
            if agent_id in self.device_statuses:
                device_status = self.device_statuses[agent_id]
                
                # Store original values for logging
                orig_cpu = device_status.cpu_usage
                orig_battery = device_status.battery_level
                
                # Gradually reduce CPU (30-70% reduction of the spike)
                reduction = device_status.cpu_usage * random.uniform(0.3, 0.7)
                device_status.cpu_usage = max(5.0, device_status.cpu_usage - reduction)
                
                # Recover some battery if it was drained
                if not device_status.battery_charging and device_status.battery_level < 50:
                    battery_recovery = random.uniform(2.0, 8.0)
                    device_status.battery_level = min(100.0, device_status.battery_level + battery_recovery)
                
                # Reduce memory usage somewhat
                memory_reduction = device_status.memory_usage * random.uniform(0.1, 0.3)
                device_status.memory_usage = max(20.0, device_status.memory_usage - memory_reduction)
                
                # Update last_updated timestamp
                device_status.last_updated = datetime.now()
                
                # Log the changes with before/after values
                print(f"Agent {agent_id} recovered - CPU: {orig_cpu:.1f}% → {device_status.cpu_usage:.1f}%, "
                      f"Battery: {orig_battery:.1f}% → {device_status.battery_level:.1f}%, "
                      f"Memory: {device_status.memory_usage:.1f}%")
                
                # Make sure changes are stored in slaves dict if agent is there
                if agent_id in self.slaves:
                    self.slaves[agent_id]["device_status"] = device_status.to_dict()
                    
                # Update capabilities to match - this ensures consistency
                if agent_id in self.slaves:
                    self.slaves[agent_id]["capabilities"]["battery"] = int(device_status.battery_level)
                    self.slaves[agent_id]["capabilities"]["cpu"] = round(device_status.cpu_usage / 10, 2)
                
                # Update agent's capabilities directly if possible
                if agent_id in self.agents and hasattr(self.agents[agent_id], "capabilities"):
                    self.agents[agent_id].capabilities["battery"] = int(device_status.battery_level)
                    self.agents[agent_id].capabilities["cpu"] = round(device_status.cpu_usage / 10, 2)
        
        return recovery_agents

    async def get_deployment_status(self, deployment_id: str = None) -> dict:
        """Get detailed deployment status with all agent information including full asset details."""
        if deployment_id is None:
            deployment_id = self.deployment_id or "current"
        
        agents_status = []
        
        # First add all registered slaves
        for slave_id, slave_info in self.slaves.items():
            device_status = self.device_statuses.get(slave_id)
            
            agent_detail = {
                "slave_id": slave_id,
                "status": slave_info.get("status", "unknown"),
                "capabilities": slave_info.get("capabilities", {}),
                "registered_at": slave_info.get("registered_at", "").isoformat() if hasattr(slave_info.get("registered_at", ""), "isoformat") else str(slave_info.get("registered_at")),
                "last_heartbeat": slave_info.get("last_heartbeat", "").isoformat() if hasattr(slave_info.get("last_heartbeat", ""), "isoformat") else str(slave_info.get("last_heartbeat")),
                "assigned_tasks": slave_info.get("assigned_tasks", []),
                "completed_tasks": slave_info.get("completed_tasks", 0),
                "failed_tasks": slave_info.get("failed_tasks", 0),
                "device_info": None,
                "ring_assignment": None,
                "asset": self.agent_to_asset.get(slave_id)  # Include full asset data
            }
            
            if device_status:
                agent_detail["device_info"] = {
                    "name": device_status.device_name,
                    "battery_level": device_status.battery_level,
                    "battery_charging": device_status.battery_charging,
                    "cpu_usage": device_status.cpu_usage,
                    "memory_usage": device_status.memory_usage,
                    "disk_usage": device_status.disk_usage,
                    "os_version": device_status.os_version,
                    "is_healthy": device_status.is_healthy()
                }
                agent_detail["ring_assignment"] = device_status.assigned_ring.value
            elif slave_info.get("device_status"):
                # If there's device_status in slave_info but not in self.device_statuses
                try:
                    ds = slave_info["device_status"]
                    agent_detail["device_info"] = {
                        "name": ds.get("device_name", f"Agent-{slave_id[-6:]}"),
                        "battery_level": ds.get("battery_level", 0),
                        "battery_charging": ds.get("battery_charging", False),
                        "cpu_usage": ds.get("cpu_usage", 0),
                        "memory_usage": ds.get("memory_usage", 0),
                        "disk_usage": ds.get("disk_usage", 0),
                        "os_version": ds.get("os_version", "Unknown"),
                        "is_healthy": True  # Assume healthy for now
                    }
                except Exception as e:
                    logger.error(f"Error parsing device status from slave_info: {e}")
            
            agents_status.append(agent_detail)
        
        # Now add any agents from self.agents that aren't in self.slaves yet
        for agent_id, agent in self.agents.items():
            if agent_id not in self.slaves:
                # Add a simpler status for agents that haven't fully registered
                agent_detail = {
                    "slave_id": agent_id,
                    "status": "spawned",  # Special status for spawned but not fully registered
                    "capabilities": getattr(agent, "capabilities", {}),
                    "registered_at": datetime.now().isoformat(),  # Just use current time
                    "last_heartbeat": datetime.now().isoformat(),  # Just use current time
                    "assigned_tasks": [],
                    "completed_tasks": 0,
                    "failed_tasks": 0,
                    "device_info": {
                        "name": f"Agent-{agent_id[-6:]}",  # Use shortened agent ID
                        "battery_level": None,
                        "cpu_usage": None,
                        "memory_usage": None,
                        "is_healthy": True  # Assume healthy initially
                    },
                    "ring_assignment": "unassigned",
                    "asset": self.agent_to_asset.get(agent_id)  # Include full asset data
                }
                agents_status.append(agent_detail)
        
        # Calculate active/idle agents including those from self.agents
        active_agents = len([s for s in self.slaves.values() if s["status"] == "busy"])
        idle_agents = len([s for s in self.slaves.values() if s["status"] == "idle"])
        # Add the agents that aren't in self.slaves yet (from self.agents)
        spawned_not_registered = len([aid for aid in self.agents.keys() if aid not in self.slaves])
        idle_agents += spawned_not_registered  # Consider them idle initially
        
        # Add a comprehensive asset list with their agent IDs
        assets = []
        for agent_id, asset in self.agent_to_asset.items():
            if asset:  # Some agents might not have an associated asset
                asset_status = {
                    "agent_id": agent_id,
                    "asset_data": asset,
                    "agent_status": "unknown"
                }
                
                # Add agent status if available
                if agent_id in self.slaves:
                    asset_status["agent_status"] = self.slaves[agent_id].get("status", "unknown")
                elif agent_id in self.agents:
                    asset_status["agent_status"] = "spawned"
                
                assets.append(asset_status)
        
        return {
            "deployment_id": deployment_id,
            "status": "active" if self.deployment_active else "completed",
            "start_time": self.deployment_start_time.isoformat() if self.deployment_start_time else None,
            "total_agents": len(self.slaves) + spawned_not_registered,  # Include all agents
            "active_agents": active_agents,
            "idle_agents": idle_agents,
            "healthy_devices": len([d for d in self.device_statuses.values() if d.is_healthy()]),
            "agents": agents_status,
            "assets": assets,  # Add comprehensive asset list
            "ring_distribution": {ring.value: len(self.ring_assignments.get(ring, [])) for ring in RingType},
            "spawned_agents": list(self.agents.keys()),  # Add this for debugging
            "registered_slaves": list(self.slaves.keys())  # Add this for debugging
        }
    
    async def complete_deployment(self, deployment_id: str) -> dict:
        """Mark deployment as complete and return all agent statuses."""
        if self.deployment_id != deployment_id:
            logger.warning(f"Deployment ID mismatch: {deployment_id}")
            return {"error": "deployment_id mismatch"}
        
        self.deployment_active = False
        deployment_duration = (datetime.now() - self.deployment_start_time).total_seconds() if self.deployment_start_time else 0
        
        # Simulate recovery of some agents after deployment completes
        recovered_agents = await self._simulate_agent_recovery()
        
        logger.info(f"Deployment {deployment_id} completed in {deployment_duration}s, recovered {len(recovered_agents)} agents")
        
        # Return full deployment status with all agent details
        result = await self.get_deployment_status(deployment_id)
        # Add recovery info
        result["recovered_agents"] = recovered_agents
        return result
    
    async def _simulate_agent_recovery(self):
        """Simulate some agents recovering to normal metrics after deployment."""
        # Select some agents to recover (40-80% of them)
        recovery_agent_count = max(1, int(len(self.agents) * random.uniform(0.4, 0.8)))
        recovery_agents = random.sample(list(self.agents.keys()), 
                                       min(recovery_agent_count, len(self.agents)))
        
        print(f"Simulating recovery for {len(recovery_agents)}/{len(self.agents)} agents")
        
        for agent_id in recovery_agents:
            if agent_id in self.device_statuses:
                device_status = self.device_statuses[agent_id]
                
                # Store original values for logging
                orig_cpu = device_status.cpu_usage
                orig_battery = device_status.battery_level
                
                # Gradually reduce CPU (30-70% reduction of the spike)
                reduction = device_status.cpu_usage * random.uniform(0.3, 0.7)
                device_status.cpu_usage = max(5.0, device_status.cpu_usage - reduction)
                
                # Recover some battery if it was drained
                if not device_status.battery_charging and device_status.battery_level < 50:
                    battery_recovery = random.uniform(2.0, 8.0)
                    device_status.battery_level = min(100.0, device_status.battery_level + battery_recovery)
                
                # Reduce memory usage somewhat
                memory_reduction = device_status.memory_usage * random.uniform(0.1, 0.3)
                device_status.memory_usage = max(20.0, device_status.memory_usage - memory_reduction)
                
                # Update last_updated timestamp
                device_status.last_updated = datetime.now()
                
                # Log the changes with before/after values
                print(f"Agent {agent_id} recovered - CPU: {orig_cpu:.1f}% → {device_status.cpu_usage:.1f}%, "
                      f"Battery: {orig_battery:.1f}% → {device_status.battery_level:.1f}%, "
                      f"Memory: {device_status.memory_usage:.1f}%")
                
                # Make sure changes are stored in slaves dict if agent is there
                if agent_id in self.slaves:
                    self.slaves[agent_id]["device_status"] = device_status.to_dict()
                    
                # Update capabilities to match - this ensures consistency
                if agent_id in self.slaves:
                    self.slaves[agent_id]["capabilities"]["battery"] = int(device_status.battery_level)
                    self.slaves[agent_id]["capabilities"]["cpu"] = round(device_status.cpu_usage / 10, 2)
                
                # Update agent's capabilities directly if possible
                if agent_id in self.agents and hasattr(self.agents[agent_id], "capabilities"):
                    self.agents[agent_id].capabilities["battery"] = int(device_status.battery_level)
                    self.agents[agent_id].capabilities["cpu"] = round(device_status.cpu_usage / 10, 2)
        
        return recovery_agents

    async def get_deployment_status(self, deployment_id: str = None) -> dict:
        """Get detailed deployment status with all agent information including full asset details."""
        if deployment_id is None:
            deployment_id = self.deployment_id or "current"
        
        agents_status = []
        
        # First add all registered slaves
        for slave_id, slave_info in self.slaves.items():
            device_status = self.device_statuses.get(slave_id)
            
            agent_detail = {
                "slave_id": slave_id,
                "status": slave_info.get("status", "unknown"),
                "capabilities": slave_info.get("capabilities", {}),
                "registered_at": slave_info.get("registered_at", "").isoformat() if hasattr(slave_info.get("registered_at", ""), "isoformat") else str(slave_info.get("registered_at")),
                "last_heartbeat": slave_info.get("last_heartbeat", "").isoformat() if hasattr(slave_info.get("last_heartbeat", ""), "isoformat") else str(slave_info.get("last_heartbeat")),
                "assigned_tasks": slave_info.get("assigned_tasks", []),
                "completed_tasks": slave_info.get("completed_tasks", 0),
                "failed_tasks": slave_info.get("failed_tasks", 0),
                "device_info": None,
                "ring_assignment": None,
                "asset": self.agent_to_asset.get(slave_id)  # Include full asset data
            }
            
            if device_status:
                agent_detail["device_info"] = {
                    "name": device_status.device_name,
                    "battery_level": device_status.battery_level,
                    "battery_charging": device_status.battery_charging,
                    "cpu_usage": device_status.cpu_usage,
                    "memory_usage": device_status.memory_usage,
                    "disk_usage": device_status.disk_usage,
                    "os_version": device_status.os_version,
                    "is_healthy": device_status.is_healthy()
                }
                agent_detail["ring_assignment"] = device_status.assigned_ring.value
            elif slave_info.get("device_status"):
                # If there's device_status in slave_info but not in self.device_statuses
                try:
                    ds = slave_info["device_status"]
                    agent_detail["device_info"] = {
                        "name": ds.get("device_name", f"Agent-{slave_id[-6:]}"),
                        "battery_level": ds.get("battery_level", 0),
                        "battery_charging": ds.get("battery_charging", False),
                        "cpu_usage": ds.get("cpu_usage", 0),
                        "memory_usage": ds.get("memory_usage", 0),
                        "disk_usage": ds.get("disk_usage", 0),
                        "os_version": ds.get("os_version", "Unknown"),
                        "is_healthy": True  # Assume healthy for now
                    }
                except Exception as e:
                    logger.error(f"Error parsing device status from slave_info: {e}")
            
            agents_status.append(agent_detail)
        
        # Now add any agents from self.agents that aren't in self.slaves yet
        for agent_id, agent in self.agents.items():
            if agent_id not in self.slaves:
                # Add a simpler status for agents that haven't fully registered
                agent_detail = {
                    "slave_id": agent_id,
                    "status": "spawned",  # Special status for spawned but not fully registered
                    "capabilities": getattr(agent, "capabilities", {}),
                    "registered_at": datetime.now().isoformat(),  # Just use current time
                    "last_heartbeat": datetime.now().isoformat(),  # Just use current time
                    "assigned_tasks": [],
                    "completed_tasks": 0,
                    "failed_tasks": 0,
                    "device_info": {
                        "name": f"Agent-{agent_id[-6:]}",  # Use shortened agent ID
                        "battery_level": None,
                        "cpu_usage": None,
                        "memory_usage": None,
                        "is_healthy": True  # Assume healthy initially
                    },
                    "ring_assignment": "unassigned",
                    "asset": self.agent_to_asset.get(agent_id)  # Include full asset data
                }
                agents_status.append(agent_detail)
        
        # Calculate active/idle agents including those from self.agents
        active_agents = len([s for s in self.slaves.values() if s["status"] == "busy"])
        idle_agents = len([s for s in self.slaves.values() if s["status"] == "idle"])
        # Add the agents that aren't in self.slaves yet (from self.agents)
        spawned_not_registered = len([aid for aid in self.agents.keys() if aid not in self.slaves])
        idle_agents += spawned_not_registered  # Consider them idle initially
        
        # Add a comprehensive asset list with their agent IDs
        assets = []
        for agent_id, asset in self.agent_to_asset.items():
            if asset:  # Some agents might not have an associated asset
                asset_status = {
                    "agent_id": agent_id,
                    "asset_data": asset,
                    "agent_status": "unknown"
                }
                
                # Add agent status if available
                if agent_id in self.slaves:
                    asset_status["agent_status"] = self.slaves[agent_id].get("status", "unknown")
                elif agent_id in self.agents:
                    asset_status["agent_status"] = "spawned"
                
                assets.append(asset_status)
        
        return {
            "deployment_id": deployment_id,
            "status": "active" if self.deployment_active else "completed",
            "start_time": self.deployment_start_time.isoformat() if self.deployment_start_time else None,
            "total_agents": len(self.slaves) + spawned_not_registered,  # Include all agents
            "active_agents": active_agents,
            "idle_agents": idle_agents,
            "healthy_devices": len([d for d in self.device_statuses.values() if d.is_healthy()]),
            "agents": agents_status,
            "assets": assets,  # Add comprehensive asset list
            "ring_distribution": {ring.value: len(self.ring_assignments.get(ring, [])) for ring in RingType},
            "spawned_agents": list(self.agents.keys()),  # Add this for debugging
            "registered_slaves": list(self.slaves.keys())  # Add this for debugging
        }
    
    async def complete_deployment(self, deployment_id: str) -> dict:
        """Mark deployment as complete and return all agent statuses."""
        if self.deployment_id != deployment_id:
            logger.warning(f"Deployment ID mismatch: {deployment_id}")
            return {"error": "deployment_id mismatch"}
        
        self.deployment_active = False
        deployment_duration = (datetime.now() - self.deployment_start_time).total_seconds() if self.deployment_start_time else 0
        
        # Simulate recovery of some agents after deployment completes
        recovered_agents = await self._simulate_agent_recovery()
        
        logger.info(f"Deployment {deployment_id} completed in {deployment_duration}s, recovered {len(recovered_agents)} agents")
        
        # Return full deployment status with all agent details
        result = await self.get_deployment_status(deployment_id)
        # Add recovery info
        result["recovered_agents"] = recovered_agents
        return result
    
    async def _simulate_agent_recovery(self):
        """Simulate some agents recovering to normal metrics after deployment."""
        # Select some agents to recover (40-80% of them)
        recovery_agent_count = max(1, int(len(self.agents) * random.uniform(0.4, 0.8)))
        recovery_agents = random.sample(list(self.agents.keys()), 
                                       min(recovery_agent_count, len(self.agents)))
        
        print(f"Simulating recovery for {len(recovery_agents)}/{len(self.agents)} agents")
        
        for agent_id in recovery_agents:
            if agent_id in self.device_statuses:
                device_status = self.device_statuses[agent_id]
                
                # Store original values for logging
                orig_cpu = device_status.cpu_usage
                orig_battery = device_status.battery_level
                
                # Gradually reduce CPU (30-70% reduction of the spike)
                reduction = device_status.cpu_usage * random.uniform(0.3, 0.7)
                device_status.cpu_usage = max(5.0, device_status.cpu_usage - reduction)
                
                # Recover some battery if it was drained
                if not device_status.battery_charging and device_status.battery_level < 50:
                    battery_recovery = random.uniform(2.0, 8.0)
                    device_status.battery_level = min(100.0, device_status.battery_level + battery_recovery)
                
                # Reduce memory usage somewhat
                memory_reduction = device_status.memory_usage * random.uniform(0.1, 0.3)
                device_status.memory_usage = max(20.0, device_status.memory_usage - memory_reduction)
                
                # Update last_updated timestamp
                device_status.last_updated = datetime.now()
                
                # Log the changes with before/after values
                print(f"Agent {agent_id} recovered - CPU: {orig_cpu:.1f}% → {device_status.cpu_usage:.1f}%, "
                      f"Battery: {orig_battery:.1f}% → {device_status.battery_level:.1f}%, "
                      f"Memory: {device_status.memory_usage:.1f}%")
                
                # Make sure changes are stored in slaves dict if agent is there
                if agent_id in self.slaves:
                    self.slaves[agent_id]["device_status"] = device_status.to_dict()
                    
                # Update capabilities to match - this ensures consistency
                if agent_id in self.slaves:
                    self.slaves[agent_id]["capabilities"]["battery"] = int(device_status.battery_level)
                    self.slaves[agent_id]["capabilities"]["cpu"] = round(device_status.cpu_usage / 10, 2)
                
                # Update agent's capabilities directly if possible
                if agent_id in self.agents and hasattr(self.agents[agent_id], "capabilities"):
                    self.agents[agent_id].capabilities["battery"] = int(device_status.battery_level)
                    self.agents[agent_id].capabilities["cpu"] = round(device_status.cpu_usage / 10, 2)
        
        return recovery_agents

    async def get_deployment_status(self, deployment_id: str = None) -> dict:
        """Get detailed deployment status with all agent information including full asset details."""
        if deployment_id is None:
            deployment_id = self.deployment_id or "current"
        
        agents_status = []
        
        # First add all registered slaves
        for slave_id, slave_info in self.slaves.items():
            device_status = self.device_statuses.get(slave_id)
            
            agent_detail = {
                "slave_id": slave_id,
                "status": slave_info.get("status", "unknown"),
                "capabilities": slave_info.get("capabilities", {}),
                "registered_at": slave_info.get("registered_at", "").isoformat() if hasattr(slave_info.get("registered_at", ""), "isoformat") else str(slave_info.get("registered_at")),
                "last_heartbeat": slave_info.get("last_heartbeat", "").isoformat() if hasattr(slave_info.get("last_heartbeat", ""), "isoformat") else str(slave_info.get("last_heartbeat")),
                "assigned_tasks": slave_info.get("assigned_tasks", []),
                "completed_tasks": slave_info.get("completed_tasks", 0),
                "failed_tasks": slave_info.get("failed_tasks", 0),
                "device_info": None,
                "ring_assignment": None,
                "asset": self.agent_to_asset.get(slave_id)  # Include full asset data
            }
            
            if device_status:
                agent_detail["device_info"] = {
                    "name": device_status.device_name,
                    "battery_level": device_status.battery_level,
                    "battery_charging": device_status.battery_charging,
                    "cpu_usage": device_status.cpu_usage,
                    "memory_usage": device_status.memory_usage,
                    "disk_usage": device_status.disk_usage,
                    "os_version": device_status.os_version,
                    "is_healthy": device_status.is_healthy()
                }
                agent_detail["ring_assignment"] = device_status.assigned_ring.value
            elif slave_info.get("device_status"):
                # If there's device_status in slave_info but not in self.device_statuses
                try:
                    ds = slave_info["device_status"]
                    agent_detail["device_info"] = {
                        "name": ds.get("device_name", f"Agent-{slave_id[-6:]}"),
                        "battery_level": ds.get("battery_level", 0),
                        "battery_charging": ds.get("battery_charging", False),
                        "cpu_usage": ds.get("cpu_usage", 0),
                        "memory_usage": ds.get("memory_usage", 0),
                        "disk_usage": ds.get("disk_usage", 0),
                        "os_version": ds.get("os_version", "Unknown"),
                        "is_healthy": True  # Assume healthy for now
                    }
                except Exception as e:
                    logger.error(f"Error parsing device status from slave_info: {e}")
            
            agents_status.append(agent_detail)
        
        # Now add any agents from self.agents that aren't in self.slaves yet
        for agent_id, agent in self.agents.items():
            if agent_id not in self.slaves:
                # Add a simpler status for agents that haven't fully registered
                agent_detail = {
                    "slave_id": agent_id,
                    "status": "spawned",  # Special status for spawned but not fully registered
                    "capabilities": getattr(agent, "capabilities", {}),
                    "registered_at": datetime.now().isoformat(),  # Just use current time
                    "last_heartbeat": datetime.now().isoformat(),  # Just use current time
                    "assigned_tasks": [],
                    "completed_tasks": 0,
                    "failed_tasks": 0,
                    "device_info": {
                        "name": f"Agent-{agent_id[-6:]}",  # Use shortened agent ID
                        "battery_level": None,
                        "cpu_usage": None,
                        "memory_usage": None,
                        "is_healthy": True  # Assume healthy initially
                    },
                    "ring_assignment": "unassigned",
                    "asset": self.agent_to_asset.get(agent_id)  # Include full asset data
                }
                agents_status.append(agent_detail)
        
        # Calculate active/idle agents including those from self.agents
        active_agents = len([s for s in self.slaves.values() if s["status"] == "busy"])
        idle_agents = len([s for s in self.slaves.values() if s["status"] == "idle"])
        # Add the agents that aren't in self.slaves yet (from self.agents)
        spawned_not_registered = len([aid for aid in self.agents.keys() if aid not in self.slaves])
        idle_agents += spawned_not_registered  # Consider them idle initially
        
        # Add a comprehensive asset list with their agent IDs
        assets = []
        for agent_id, asset in self.agent_to_asset.items():
            if asset:  # Some agents might not have an associated asset
                asset_status = {
                    "agent_id": agent_id,
                    "asset_data": asset,
                    "agent_status": "unknown"
                }
                
                # Add agent status if available
                if agent_id in self.slaves:
                    asset_status["agent_status"] = self.slaves[agent_id].get("status", "unknown")
                elif agent_id in self.agents:
                    asset_status["agent_status"] = "spawned"
                
                assets.append(asset_status)
        
        return {
            "deployment_id": deployment_id,
            "status": "active" if self.deployment_active else "completed",
            "start_time": self.deployment_start_time.isoformat() if self.deployment_start_time else None,
            "total_agents": len(self.slaves) + spawned_not_registered,  # Include all agents
            "active_agents": active_agents,
            "idle_agents": idle_agents,
            "healthy_devices": len([d for d in self.device_statuses.values() if d.is_healthy()]),
            "agents": agents_status,
            "assets": assets,  # Add comprehensive asset list
            "ring_distribution": {ring.value: len(self.ring_assignments.get(ring, [])) for ring in RingType},
            "spawned_agents": list(self.agents.keys()),  # Add this for debugging
            "registered_slaves": list(self.slaves.keys())  # Add this for debugging
        }
    
    async def _process_messages(self):
        """Process incoming messages from slaves."""
        logger.info("Starting message processing loop")
        
        while self.running:
            try:
                message = await self.queue_manager.receive_message(
                    self.agent_id,
                    timeout=1.0
                )
                
                if message:
                    await self._handle_message(message)
                
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    
    async def _handle_message(self, message: Message):
        """Handle a message from a slave."""
        message_type = message.message_type
        sender_id = message.sender_id
        payload = message.payload
        
        logger.debug(f"Handling {message_type} from {sender_id}")
        
        if message_type == MessageType.REGISTRATION:
            await self.register_slave(
                sender_id,
                payload.get("capabilities", {}),
                payload.get("device_status")
            )
        
        elif message_type == MessageType.HEARTBEAT:
            await self._update_heartbeat(sender_id, payload.get("device_status"))
        
        elif message_type == MessageType.DEVICE_STATUS_UPDATE:
            await self._update_device_status(sender_id, payload.get("device_status"))
        
        elif message_type == MessageType.TASK_RESULT:
            await self._handle_task_result(sender_id, payload)
        
        elif message_type == MessageType.TASK_STATUS:
            await self._handle_task_status(sender_id, payload)
        
        elif message_type == MessageType.ERROR:
            await self._handle_slave_error(sender_id, payload)
    
    async def _assign_tasks(self):
        """Assign pending tasks to available slaves."""
        if not self.task_queue:
            return
        
        # Find idle slaves
        idle_slaves = [
            slave_id for slave_id, info in self.slaves.items()
            if info["status"] == "idle"
        ]
        
        if not idle_slaves:
            return
        
        # Assign tasks
        for slave_id in idle_slaves:
            if not self.task_queue:
                break
            
            task = self.task_queue.pop(0)
            task.assigned_to = slave_id
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now()
            
            self.slaves[slave_id]["status"] = "busy"
            self.slaves[slave_id]["assigned_tasks"].append(task.task_id)
            
            # Send task assignment
            await self._send_message(
                MessageType.TASK_ASSIGNMENT,
                slave_id,
                {"task": task.to_dict()}
            )
            
            logger.info(f"Task {task.task_id} assigned to slave {slave_id}")
    
    async def _handle_task_result(self, slave_id: str, payload: dict):
        """Handle task result from slave."""
        task_id = payload.get("task_id")
        result = payload.get("result")
        error = payload.get("error")
        
        if task_id not in self.tasks:
            logger.warning(f"Unknown task result received: {task_id}")
            return
        
        task = self.tasks[task_id]
        task.completed_at = datetime.now()
        
        if error:
            task.status = TaskStatus.FAILED
            task.error = error
            self.slaves[slave_id]["failed_tasks"] += 1
            logger.error(f"Task {task_id} failed: {error}")
        else:
            task.status = TaskStatus.COMPLETED
            task.result = result
            self.slaves[slave_id]["completed_tasks"] += 1
            logger.info(f"Task {task_id} completed successfully")
        
        # Update slave status
        self.slaves[slave_id]["status"] = "idle"
        if task_id in self.slaves[slave_id]["assigned_tasks"]:
            self.slaves[slave_id]["assigned_tasks"].remove(task_id)
        
        # Try to assign more tasks
        await self._assign_tasks()
    
    async def _handle_task_status(self, slave_id: str, payload: dict):
        """Handle task status update from slave."""
        task_id = payload.get("task_id")
        status = payload.get("status")
        progress = payload.get("progress", 0)
        
        if task_id in self.tasks:
            logger.debug(f"Task {task_id} status: {status} ({progress}%)")
    
    async def _handle_slave_error(self, slave_id: str, payload: dict):
        """Handle error message from slave."""
        error = payload.get("error")
        logger.error(f"Slave {slave_id} error: {error}")
        
        # Potentially reassign tasks or remove slave
        if slave_id in self.slaves:
            self.slaves[slave_id]["status"] = "error"
    
    async def _update_heartbeat(self, slave_id: str, device_status_dict: dict = None):
        """Update last heartbeat time for a slave."""
        if slave_id in self.slaves:
            self.slaves[slave_id]["last_heartbeat"] = datetime.now()
            if device_status_dict:
                await self._update_device_status(slave_id, device_status_dict)
    
    async def _update_device_status(self, slave_id: str, device_status_dict: dict):
        """Update device status for a slave."""
        if not device_status_dict:
            return
        
        try:
            device_status = DeviceStatus.from_dict(device_status_dict)
            self.device_statuses[slave_id] = device_status
            
            # Update slave info
            if slave_id in self.slaves:
                self.slaves[slave_id]["device_status"] = device_status_dict
            
            logger.debug(
                f"Device status updated for {slave_id}: "
                f"Battery={device_status.battery_level}%, CPU={device_status.cpu_usage:.1f}%, "
                f"Ring={device_status.assigned_ring.value}"
            )
        except Exception as e:
            logger.error(f"Error updating device status for {slave_id}: {e}")
    
    async def _auto_assign_ring(self, slave_id: str):
        """Automatically assign a slave to a ring based on device health."""
        if slave_id not in self.device_statuses:
            logger.warning(f"No device status for {slave_id}, cannot auto-assign ring")
            return
        
        device = self.device_statuses[slave_id]
        
        # Ring assignment logic based on device health
        if device.is_healthy():
            # Healthy devices can go to any ring
            # Distribute evenly across rings
            ring_counts = {
                RingType.CANARY: len(self.ring_assignments[RingType.CANARY]),
                RingType.DEV: len(self.ring_assignments[RingType.DEV]),
                RingType.STAGE: len(self.ring_assignments[RingType.STAGE]),
                RingType.PROD: len(self.ring_assignments[RingType.PROD]),
            }
            assigned_ring = min(ring_counts, key=ring_counts.get)
        else:
            # Unhealthy devices go to DEV or CANARY
            assigned_ring = random.choice([RingType.CANARY, RingType.DEV])
        
        await self.assign_slave_to_ring(slave_id, assigned_ring, "Auto-assignment based on device health")
    
    async def assign_slave_to_ring(self, slave_id: str, ring: RingType, reason: str = "Manual assignment"):
        """Assign a slave to a specific ring."""
        if slave_id not in self.slaves:
            logger.error(f"Cannot assign ring: slave {slave_id} not found")
            return False
        
        # Remove from old ring
        if slave_id in self.device_statuses:
            old_ring = self.device_statuses[slave_id].assigned_ring
            if old_ring in self.ring_assignments and slave_id in self.ring_assignments[old_ring]:
                self.ring_assignments[old_ring].remove(slave_id)
        
        # Add to new ring
        if ring not in self.ring_assignments:
            self.ring_assignments[ring] = []
        self.ring_assignments[ring].append(slave_id)
        
        # Update device status
        if slave_id in self.device_statuses:
            self.device_statuses[slave_id].assigned_ring = ring
        
        logger.info(f"Assigned slave {slave_id} to ring {ring.value}: {reason}")
        
        # Notify slave
        await self._send_message(
            MessageType.RING_ASSIGNMENT,
            slave_id,
            {
                "ring": ring.value,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return True
    
    async def _ring_rebalancer(self):
        """Periodically rebalance ring assignments based on device status."""
        while self.running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                logger.info("Running ring rebalancing check...")
                
                for slave_id, device in self.device_statuses.items():
                    current_ring = device.assigned_ring
                    
                    # Skip unassigned
                    if current_ring == RingType.UNASSIGNED:
                        await self._auto_assign_ring(slave_id)
                        continue
                    
                    # Move unhealthy devices out of PROD
                    if not device.is_healthy() and current_ring == RingType.PROD:
                        new_ring = random.choice([RingType.CANARY, RingType.DEV])
                        await self.assign_slave_to_ring(
                            slave_id,
                            new_ring,
                            f"Device unhealthy - moved from PROD (Battery: {device.battery_level}%, CPU: {device.cpu_usage:.1f}%)"
                        )
                    
                    # Randomly reassign some devices for testing (10% chance)
                    elif random.random() < 0.1:
                        available_rings = [RingType.CANARY, RingType.DEV, RingType.STAGE]
                        if device.is_healthy():
                            available_rings.append(RingType.PROD)
                        
                        new_ring = random.choice(available_rings)
                        if new_ring != current_ring:
                            await self.assign_slave_to_ring(
                                slave_id,
                                new_ring,
                                "Random rebalancing for load distribution"
                            )
                
                logger.info("Ring rebalancing check completed")
                
            except Exception as e:
                logger.error(f"Error in ring rebalancer: {e}")
    
    async def _heartbeat_monitor(self):
        """Monitor slave heartbeats and remove dead slaves."""
        while self.running:
            try:
                now = datetime.now()
                timeout_seconds = self.config.slave_timeout
                
                dead_slaves = []
                for slave_id, info in self.slaves.items():
                    last_heartbeat = info["last_heartbeat"]
                    if (now - last_heartbeat).total_seconds() > timeout_seconds:
                        dead_slaves.append(slave_id)
                
                for slave_id in dead_slaves:
                    logger.warning(f"Slave {slave_id} timed out, removing...")
                    await self._remove_slave(slave_id)
                
                await asyncio.sleep(self.config.slave_heartbeat_interval)
            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {e}")
    
    async def _task_monitor(self):
        """Monitor task progress and handle timeouts."""
        while self.running:
            try:
                now = datetime.now()
                timeout_seconds = self.config.task_timeout
                
                for task in self.tasks.values():
                    if task.status == TaskStatus.IN_PROGRESS and task.started_at:
                        elapsed = (now - task.started_at).total_seconds()
                        if elapsed > timeout_seconds:
                            logger.warning(f"Task {task.task_id} timed out")
                            task.status = TaskStatus.FAILED
                            task.error = "Task timeout"
                            
                            # Retry if under limit
                            if task.priority < self.config.task_retry_limit:
                                task.priority += 1
                                task.status = TaskStatus.PENDING
                                self.task_queue.append(task)
                
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Error in task monitor: {e}")
    
    async def _remove_slave(self, slave_id: str):
        """Remove a slave and reassign its tasks."""
        if slave_id not in self.slaves:
            return
        
        slave_info = self.slaves[slave_id]
        assigned_tasks = slave_info["assigned_tasks"]
        
        # Reassign tasks
        for task_id in assigned_tasks:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = TaskStatus.PENDING
                task.assigned_to = None
                self.task_queue.append(task)
                logger.info(f"Task {task_id} reassigned after slave {slave_id} removal")
        
        del self.slaves[slave_id]
        logger.info(f"Slave {slave_id} removed from cluster")
    
    async def _send_message(self, message_type: MessageType, receiver_id: str, payload: dict):
        """Send a message to a slave."""
        message = Message(
            message_type=message_type,
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            timestamp=datetime.now(),
            payload=payload,
            message_id=str(uuid.uuid4())
        )
        
        await self.queue_manager.send_message(message)
    
    async def _broadcast_shutdown(self):
        """Broadcast shutdown message to all slaves."""
        for slave_id in list(self.slaves.keys()):
            await self._send_message(
                MessageType.SHUTDOWN,
                slave_id,
                {"reason": "Master shutting down"}
            )

    def _handle_heartbeat(self, message):
        """Handle heartbeat messages from slaves."""
        try:
            slave_id = message.get('slave_id')
            capabilities = message.get('capabilities', {})
            
            # Check if this is from an agent we know about
            if slave_id and slave_id not in self.slaves:
                # Auto-register any agent we spawned that's sending heartbeats
                if slave_id in self.agents:
                    print(f"[Master] Auto-registering agent {slave_id}")
                    # Create entry in slaves dict for this agent
                    self.slaves[slave_id] = {
                        "slave_id": slave_id,
                        "capabilities": capabilities,
                        "status": "idle",
                        "registered_at": datetime.now(),
                        "last_heartbeat": datetime.now(),
                        "assigned_tasks": [],
                        "completed_tasks": 0,
                        "failed_tasks": 0
                    }
                
            # Log heartbeat for debugging
            print(f"[Master] Heartbeat from {slave_id} capabilities={capabilities}")
            
            # Update heartbeat timestamp if it's a known slave
            if slave_id in self.slaves:
                self.slaves[slave_id]["last_heartbeat"] = datetime.now()
                
        except Exception as e:
            print(f"[Master] Error handling heartbeat: {e}")
    
    def spawn_agent_random(self):
        details = getattr(self.config, "random_agent_details", lambda: {})()
        if not details:
            # fallback minimal details
            details = {
                "slave_id": f"slave-{uuid.uuid4().hex[:8]}",
                "capabilities": {"tasks": ["health_check", "monitor"], "site": "unknown"}
            }

        slave_id = details["slave_id"]
        agent = SlaveAgent(
            slave_id=slave_id,
            master_id=self.agent_id,
            capabilities=details["capabilities"],
            config=self.config,
            queue_manager=self.queue_manager
        )
        self.agents[slave_id] = agent
        task = agent.start_in_background()
        self._agent_tasks[slave_id] = task
        print(f"[Master] spawned agent {slave_id}")
        return slave_id

    async def on_asset_added(self, asset: dict):
        """Called by UI when an asset is added. Spawn one agent with random details."""
        print(f"[Master] asset added: {asset}. Spawning an agent to handle it.")
        agent_id = self.spawn_agent_random()
        
        # Store the relationship between agent and asset
        self.agent_to_asset[agent_id] = asset
        
        # Return the agent ID for tracking
        return agent_id

# ------------------------------
# Minimal runnable demo entrypoint
# ------------------------------
async def _demo_run(duration: float = 12.0):
    """Demo runner: starts master, spawns default agents, simulates UI asset add, then stops."""
    # Build config with safe defaults if missing attrs
    cfg = OrchestratorConfig()
    if not hasattr(cfg, "default_num_agents"):
        cfg.default_num_agents = getattr(cfg, "default_agents", 5)
    if not hasattr(cfg, "slave_heartbeat_interval"):
        cfg.slave_heartbeat_interval = 5.0
    if not hasattr(cfg, "slave_timeout"):
        cfg.slave_timeout = 20.0
    if not hasattr(cfg, "task_timeout"):
        cfg.task_timeout = 60.0
    cfg.master_id = getattr(cfg, "master_id", "master-001")

    master = MasterOrchestrator(cfg)

    # Start master in background so demo can continue
    start_task = asyncio.create_task(master.start())

    # spawn default agents
    num_agents = getattr(cfg, "default_num_agents", 5)
    for _ in range(num_agents):
        master.spawn_agent_random()
    
    # short pause then simulate UI adding an asset
    await asyncio.sleep(1.0)
    sample_asset = {
        "id": "5449...048",
        "name": "mmr-10180",
        "site": "HQ",
        "department": "IT"
    }
    await master.on_asset_added(sample_asset)

    # run for a while to observe heartbeats
    await asyncio.sleep(duration)
    
    # stop everything
    if hasattr(master, "stop_all_agents"):
        await master.stop_all_agents()
    await master.stop()
    
    # cancel start_task if still running
    if not start_task.done():
        start_task.cancel()
        try:
            await start_task
        except Exception:
            pass

# ------------------------------
# CLI-friendly entrypoint for quick demo
# ------------------------------
def main():
    """CLI-friendly entrypoint for quick demo."""
    try:
        asyncio.run(_demo_run())
    except KeyboardInterrupt:
        print("Demo interrupted")

if __name__ == "__main__":
    main()
