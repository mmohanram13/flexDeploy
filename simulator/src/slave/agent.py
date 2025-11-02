"""Slave agent that executes tasks assigned by the master."""

import asyncio
import logging
import uuid
import random
import time
from datetime import datetime
from typing import Any, Callable, Dict, Optional

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


logger = logging.getLogger(__name__)


class SlaveAgent:
    """Slave agent that executes tasks assigned by the master orchestrator."""
    
    def __init__(
        self,
        slave_id: str,
        master_id: str,
        capabilities: Dict[str, Any],
        config: OrchestratorConfig,
        queue_manager: QueueManager,
        device_name: Optional[str] = None,
        os_version: Optional[str] = None,
        app_version: Optional[str] = None
    ):
        self.slave_id = slave_id
        self.master_id = master_id
        self.capabilities = capabilities
        self.config = config
        self.queue_manager = queue_manager
        
        # Device status with initial random values
        self.device_status = DeviceStatus(
            slave_id=slave_id,
            battery_level=random.randint(30, 100),
            battery_charging=random.choice([True, False]),
            cpu_usage=random.uniform(10.0, 60.0),
            memory_usage=random.uniform(30.0, 70.0),
            disk_usage=random.uniform(40.0, 80.0),
            assigned_ring=RingType.UNASSIGNED,
            device_name=device_name or f"Device-{slave_id[:8]}",
            os_version=os_version or "1.0.0",
            app_version=app_version or "1.0.0"
        )
        
        # Task handlers
        self.task_handlers: Dict[str, Callable] = {}
        
        # State management
        self.current_task: Optional[Task] = None
        self.status = "idle"
        self.running = False
        self._task: Optional[asyncio.Task] = None
        
        logger.info(f"Slave agent initialized: {self.slave_id} - Device: {self.device_status.device_name}")
    
    def register_task_handler(self, task_type: str, handler: Callable):
        """Register a handler function for a task type."""
        self.task_handlers[task_type] = handler
        logger.info(f"Task handler registered for type: {task_type}")
    
    async def start(self):
        """Start the slave agent."""
        if self.running:
            logger.warning(f"Slave {self.slave_id} already running")
            return
        
        self.running = True
        logger.info(f"Starting slave agent {self.slave_id}...")
        
        # Register with master
        await self._register_with_master()
        
        # Start background tasks
        self._heartbeat_task = asyncio.create_task(self._send_heartbeats())
        self._message_task = asyncio.create_task(self._process_messages())
        self._device_monitor_task = asyncio.create_task(self._monitor_device_status())
        
        # Wait for tasks
        await asyncio.gather(self._heartbeat_task, self._message_task, self._device_monitor_task)
    
    async def stop(self):
        """Stop the slave agent."""
        logger.info(f"Stopping slave agent {self.slave_id}...")
        self.running = False
        
        # Cancel background tasks
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._message_task:
            self._message_task.cancel()
        if self._device_monitor_task:
            self._device_monitor_task.cancel()
        
        self.status = "stopped"
        logger.info(f"Slave agent {self.slave_id} stopped")
    
    async def _register_with_master(self):
        """Register this slave with the master orchestrator."""
        await self._send_message(
            MessageType.REGISTRATION,
            {
                "capabilities": self.capabilities,
                "status": self.status,
                "device_status": self.device_status.to_dict()
            }
        )
        logger.info(f"Registration request sent to master {self.master_id}")
    
    async def _send_heartbeats(self):
        """Send periodic heartbeat messages to master."""
        while self.running:
            try:
                await self._send_message(
                    MessageType.HEARTBEAT,
                    {
                        "status": self.status,
                        "current_task": self.current_task.task_id if self.current_task else None,
                        "device_status": self.device_status.to_dict()
                    }
                )
                await asyncio.sleep(self.config.slave_heartbeat_interval)
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")
                await asyncio.sleep(1)
    
    async def _monitor_device_status(self):
        """Monitor and update device status periodically."""
        while self.running:
            try:
                # Update device metrics (simulate changes)
                self.device_status.update_metrics()
                
                # Send device status update to master every 10 seconds
                await self._send_message(
                    MessageType.DEVICE_STATUS_UPDATE,
                    {
                        "device_status": self.device_status.to_dict()
                    }
                )
                
                logger.debug(
                    f"Device status - Battery: {self.device_status.battery_level}%, "
                    f"CPU: {self.device_status.cpu_usage:.1f}%, "
                    f"Ring: {self.device_status.assigned_ring.value}"
                )
                
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Error monitoring device status: {e}")
                await asyncio.sleep(1)
    
    async def _process_messages(self):
        """Process incoming messages from master."""
        logger.info(f"Slave {self.slave_id} starting message processing")
        
        while self.running:
            try:
                message = await self.queue_manager.receive_message(
                    self.slave_id,
                    timeout=1.0
                )
                
                if message:
                    await self._handle_message(message)
                
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    
    async def _handle_message(self, message: Message):
        """Handle a message from the master."""
        message_type = message.message_type
        payload = message.payload
        
        logger.debug(f"Handling {message_type} message")
        
        if message_type == MessageType.TASK_ASSIGNMENT:
            await self._handle_task_assignment(payload)
        
        elif message_type == MessageType.RING_ASSIGNMENT:
            await self._handle_ring_assignment(payload)
        
        elif message_type == MessageType.SHUTDOWN:
            logger.info(f"Shutdown request received: {payload.get('reason')}")
            await self.stop()
        
        elif message_type == MessageType.ACK:
            logger.info(f"Acknowledgement received: {payload.get('message')}")
        
        elif message_type == MessageType.MODIFY_METRICS:
            await self._handle_modify_metrics(payload)
    
    async def _handle_ring_assignment(self, payload: dict):
        """Handle ring assignment from master."""
        try:
            new_ring = RingType(payload.get("ring", "unassigned"))
            old_ring = self.device_status.assigned_ring
            
            self.device_status.assigned_ring = new_ring
            self.device_status.last_updated = datetime.now()
            
            logger.info(
                f"Ring assignment changed: {old_ring.value} -> {new_ring.value} "
                f"(Reason: {payload.get('reason', 'No reason provided')})"
            )
            
            # Send acknowledgement
            await self._send_message(
                MessageType.ACK,
                {
                    "message": f"Ring assignment updated to {new_ring.value}",
                    "old_ring": old_ring.value,
                    "new_ring": new_ring.value,
                    "device_status": self.device_status.to_dict()
                }
            )
        except Exception as e:
            logger.error(f"Error handling ring assignment: {e}")
            await self.report_error(f"Ring assignment failed: {str(e)}")
    
    async def _handle_task_assignment(self, payload: dict):
        """Handle a task assignment from master."""
        try:
            task_data = payload.get("task")
            if not task_data:
                logger.error("No task data in assignment message")
                return
            
            task = Task.from_dict(task_data)
            self.current_task = task
            self.status = "busy"
            
            logger.info(f"Task assigned: {task.task_id} (type: {task.task_type})")
            
            # Send status update
            await self._send_task_status(task.task_id, TaskStatus.IN_PROGRESS, 0)
            
            # Execute task
            result = await self._execute_task(task)
            
            # Send result
            await self._send_task_result(task.task_id, result, None)
            
        except Exception as e:
            logger.error(f"Error handling task assignment: {e}")
            if self.current_task:
                await self._send_task_result(
                    self.current_task.task_id,
                    None,
                    str(e)
                )
        finally:
            self.current_task = None
            self.status = "idle"
    
    async def _execute_task(self, task: Task) -> Any:
        """Execute a task using the registered handler."""
        task_type = task.task_type
        
        if task_type not in self.task_handlers:
            raise ValueError(f"No handler registered for task type: {task_type}")
        
        handler = self.task_handlers[task_type]
        
        logger.info(f"Executing task {task.task_id} of type {task_type}")
        
        try:
            # Send progress updates
            await self._send_task_status(task.task_id, TaskStatus.IN_PROGRESS, 25)
            
            # Execute the handler
            if asyncio.iscoroutinefunction(handler):
                result = await handler(task.parameters)
            else:
                result = await asyncio.to_thread(handler, task.parameters)
            
            await self._send_task_status(task.task_id, TaskStatus.IN_PROGRESS, 75)
            
            logger.info(f"Task {task.task_id} executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Task {task.task_id} execution failed: {e}")
            raise
    
    async def _send_task_result(self, task_id: str, result: Any, error: Optional[str]):
        """Send task result to master."""
        await self._send_message(
            MessageType.TASK_RESULT,
            {
                "task_id": task_id,
                "result": result,
                "error": error,
                "completed_at": datetime.now().isoformat()
            }
        )
        
        if error:
            logger.error(f"Task {task_id} failed: {error}")
        else:
            logger.info(f"Task {task_id} result sent to master")
    
    async def _send_task_status(self, task_id: str, status: TaskStatus, progress: int):
        """Send task status update to master."""
        await self._send_message(
            MessageType.TASK_STATUS,
            {
                "task_id": task_id,
                "status": status.value,
                "progress": progress
            }
        )
    
    async def _send_message(self, message_type: MessageType, payload: dict):
        """Send a message to the master."""
        message = Message(
            message_type=message_type,
            sender_id=self.slave_id,
            receiver_id=self.master_id,
            timestamp=datetime.now(),
            payload=payload,
            message_id=str(uuid.uuid4())
        )
        
        await self.queue_manager.send_message(message)
    
    async def report_error(self, error: str):
        """Report an error to the master."""
        await self._send_message(
            MessageType.ERROR,
            {
                "error": error,
                "slave_id": self.slave_id,
                "timestamp": datetime.now().isoformat()
            }
        )
        logger.error(f"Error reported to master: {error}")
    
    async def _run(self):
        """Main agent loop."""
        self.running = True
        logger.info(f"[SlaveAgent:{self.slave_id}] started with capabilities={self.capabilities}")
        try:
            while self.running:
                # Send heartbeat message
                msg = {
                    "type": "HEARTBEAT",
                    "slave_id": self.slave_id,
                    "timestamp": time.time(),
                    "capabilities": self.capabilities,
                    "device_status": {
                        "slave_id": self.slave_id,
                        "battery_level": self.device_status.battery_level,
                        "battery_charging": self.device_status.battery_charging,
                        "cpu_usage": self.device_status.cpu_usage,
                        "memory_usage": self.device_status.memory_usage,
                        "disk_usage": self.device_status.disk_usage,
                        "device_name": self.capabilities.get("name", f"Agent-{self.slave_id[-6:]}"),
                        "os_version": self.capabilities.get("osName", "Unknown"),
                        "last_updated": datetime.now().isoformat()
                    }
                }
                
                try:
                    await self.queue_manager.publish("heartbeat", msg)
                except Exception:
                    pass  # Ignore queue failures
                
                await asyncio.sleep(self.config.slave_heartbeat_interval)
        finally:
            logger.info(f"[SlaveAgent:{self.slave_id}] stopped")

    def start_in_background(self):
        """Create a background asyncio task and return it."""
        loop = asyncio.get_event_loop()
        self._task = loop.create_task(self._run())
        return self._task

    async def stop(self):
        """Stop the slave agent."""
        logger.info(f"Stopping slave agent {self.slave_id}...")
        self.running = False
        if self._task:
            await self._task
        self.status = "stopped"
        logger.info(f"Slave agent {self.slave_id} stopped")

    def _apply_metric_changes(self, changes: dict):
        """Apply metric changes as instructed by the master."""
        logger.info(f"[SlaveAgent:{self.slave_id}] Applying metric changes: {changes}")
        
        orig_cpu = self.device_status.cpu_usage
        orig_battery = self.device_status.battery_level
        orig_memory = self.device_status.memory_usage
        
        if "cpu_change" in changes:
            self.device_status.cpu_usage = min(95.0, self.device_status.cpu_usage + changes["cpu_change"])
        
        if "battery_change" in changes:
            self.device_status.battery_level = max(5.0, min(100.0, self.device_status.battery_level + changes["battery_change"]))
        
        if "memory_change" in changes:
            self.device_status.memory_usage = min(90.0, self.device_status.memory_usage + changes["memory_change"])
        
        logger.info(
            f"[SlaveAgent:{self.slave_id}] Metrics changed - "
            f"CPU: {orig_cpu:.1f}% → {self.device_status.cpu_usage:.1f}%, "
            f"Battery: {orig_battery:.1f}% → {self.device_status.battery_level:.1f}%, "
            f"Memory: {orig_memory:.1f}% → {self.device_status.memory_usage:.1f}%"
        )
