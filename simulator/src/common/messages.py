"""Message types for master-slave communication."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
import random


class MessageType(Enum):
    """Types of messages exchanged between master and slave agents."""
    
    TASK_ASSIGNMENT = "task_assignment"
    TASK_RESULT = "task_result"
    TASK_STATUS = "task_status"
    HEARTBEAT = "heartbeat"
    SHUTDOWN = "shutdown"
    ERROR = "error"
    REGISTRATION = "registration"
    ACK = "acknowledgement"
    RING_ASSIGNMENT = "ring_assignment"
    DEVICE_STATUS_UPDATE = "device_status_update"
    MODIFY_METRICS = "modify_metrics"  # New message type for instructing metric changes


class TaskStatus(Enum):
    """Status of a task."""
    
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RingType(Enum):
    """Deployment rings for progressive rollout."""
    
    CANARY = "canary"
    DEV = "dev"
    STAGE = "stage"
    PROD = "prod"
    UNASSIGNED = "unassigned"


@dataclass
class DeviceStatus:
    """Device status information for slave agents."""
    
    slave_id: str
    battery_level: int  # 0-100
    battery_charging: bool
    cpu_usage: float  # 0-100
    memory_usage: float  # 0-100
    disk_usage: float  # 0-100
    assigned_ring: RingType = RingType.UNASSIGNED
    device_name: Optional[str] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert device status to dictionary."""
        return {
            "slave_id": self.slave_id,
            "battery_level": self.battery_level,
            "battery_charging": self.battery_charging,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "disk_usage": self.disk_usage,
            "assigned_ring": self.assigned_ring.value,
            "device_name": self.device_name,
            "os_version": self.os_version,
            "app_version": self.app_version,
            "last_updated": self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeviceStatus":
        """Create device status from dictionary."""
        return cls(
            slave_id=data["slave_id"],
            battery_level=data["battery_level"],
            battery_charging=data["battery_charging"],
            cpu_usage=data["cpu_usage"],
            memory_usage=data["memory_usage"],
            disk_usage=data["disk_usage"],
            assigned_ring=RingType(data.get("assigned_ring", "unassigned")),
            device_name=data.get("device_name"),
            os_version=data.get("os_version"),
            app_version=data.get("app_version"),
            last_updated=datetime.fromisoformat(data.get("last_updated", datetime.now().isoformat()))
        )
    
    def is_healthy(self) -> bool:
        """Check if device is healthy for deployment."""
        return (
            self.battery_level > 20 and
            self.cpu_usage < 80 and
            self.memory_usage < 85
        )
    
    def update_metrics(self):
        """Simulate random metric updates."""
        # Simulate battery drain or charge
        if self.battery_charging:
            self.battery_level = min(100, self.battery_level + random.randint(1, 5))
        else:
            self.battery_level = max(0, self.battery_level - random.randint(0, 3))
        
        # Simulate CPU fluctuation
        self.cpu_usage = max(5.0, min(95.0, self.cpu_usage + random.uniform(-10, 10)))
        
        # Simulate memory fluctuation
        self.memory_usage = max(20.0, min(90.0, self.memory_usage + random.uniform(-5, 5)))
        
        # Simulate disk usage (slowly increasing)
        self.disk_usage = min(95.0, self.disk_usage + random.uniform(0, 0.5))
        
        self.last_updated = datetime.now()


@dataclass
class Message:
    """Base message structure for communication."""
    
    message_type: MessageType
    sender_id: str
    receiver_id: str
    timestamp: datetime
    payload: dict[str, Any]
    message_id: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "message_type": self.message_type.value,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "message_id": self.message_id
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """Create message from dictionary."""
        return cls(
            message_type=MessageType(data["message_type"]),
            sender_id=data["sender_id"],
            receiver_id=data["receiver_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            payload=data["payload"],
            message_id=data.get("message_id")
        )


@dataclass
class Task:
    """Task definition for slave agents."""
    
    task_id: str
    task_type: str
    parameters: dict[str, Any]
    priority: int = 0
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "parameters": self.parameters,
            "priority": self.priority,
            "status": self.status.value,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        """Create task from dictionary."""
        return cls(
            task_id=data["task_id"],
            task_type=data["task_type"],
            parameters=data["parameters"],
            priority=data.get("priority", 0),
            status=TaskStatus(data.get("status", "pending")),
            assigned_to=data.get("assigned_to"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            result=data.get("result"),
            error=data.get("error")
        )
