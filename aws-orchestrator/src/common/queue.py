"""Queue implementations for message passing."""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, Any, Callable, Dict, List
from datetime import datetime
from .messages import Message


logger = logging.getLogger(__name__)


class MessageQueue(ABC):
    """Abstract base class for message queues."""
    
    @abstractmethod
    async def send(self, message: Message) -> bool:
        """Send a message to the queue."""
        pass
    
    @abstractmethod
    async def receive(self, timeout: Optional[float] = None) -> Optional[Message]:
        """Receive a message from the queue."""
        pass
    
    @abstractmethod
    async def size(self) -> int:
        """Get the current size of the queue."""
        pass


class InMemoryQueue(MessageQueue):
    """In-memory implementation of message queue using asyncio.Queue."""
    
    def __init__(self, maxsize: int = 0):
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._stats = {
            "sent": 0,
            "received": 0,
            "dropped": 0
        }
    
    async def send(self, message: Message) -> bool:
        """Send a message to the queue."""
        try:
            await self.queue.put(message)
            self._stats["sent"] += 1
            logger.debug(f"Message sent: {message.message_type} from {message.sender_id}")
            return True
        except asyncio.QueueFull:
            self._stats["dropped"] += 1
            logger.warning(f"Queue full, message dropped: {message.message_type}")
            return False
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    async def receive(self, timeout: Optional[float] = None) -> Optional[Message]:
        """Receive a message from the queue."""
        try:
            if timeout:
                message = await asyncio.wait_for(self.queue.get(), timeout=timeout)
            else:
                message = await self.queue.get()
            
            self._stats["received"] += 1
            logger.debug(f"Message received: {message.message_type} to {message.receiver_id}")
            return message
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            return None
    
    async def size(self) -> int:
        """Get the current size of the queue."""
        return self.queue.qsize()
    
    def get_stats(self) -> dict[str, int]:
        """Get queue statistics."""
        return self._stats.copy()


class QueueManager:
    """Manages multiple message queues for different agents."""
    
    def __init__(self, queue_type: str = "memory", maxsize: int = 0):
        self.queue_type = queue_type
        self.maxsize = maxsize
        self.queues: dict[str, MessageQueue] = {}
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = {}
        self._loop = asyncio.get_event_loop()
    
    def get_queue(self, agent_id: str) -> MessageQueue:
        """Get or create a queue for an agent."""
        if agent_id not in self.queues:
            self.queues[agent_id] = self._create_queue()
        return self.queues[agent_id]
    
    def _create_queue(self) -> MessageQueue:
        """Create a new queue based on configuration."""
        if self.queue_type == "memory":
            return InMemoryQueue(maxsize=self.maxsize)
        else:
            raise ValueError(f"Unsupported queue type: {self.queue_type}")
    
    async def send_message(self, message: Message) -> bool:
        """Send a message to the appropriate queue."""
        queue = self.get_queue(message.receiver_id)
        return await queue.send(message)
    
    async def receive_message(self, agent_id: str, timeout: Optional[float] = None) -> Optional[Message]:
        """Receive a message from an agent's queue."""
        queue = self.get_queue(agent_id)
        return await queue.receive(timeout)
    
    def get_all_stats(self) -> dict[str, dict[str, int]]:
        """Get statistics for all queues."""
        return {
            agent_id: queue.get_stats() if isinstance(queue, InMemoryQueue) else {}
            for agent_id, queue in self.queues.items()
        }
    
    def subscribe(self, topic: str, callback: Callable[[Any], None]):
        """Subscribe a callback to a topic."""
        self._subscribers.setdefault(topic, []).append(callback)
    
    async def publish(self, topic: str, message: Any):
        """Publish a message to a topic, notifying all subscribers."""
        # Dispatch to subscribers asynchronously
        for cb in list(self._subscribers.get(topic, [])):
            # Schedule callbacks in loop without awaiting them directly
            self._loop.call_soon(cb, message)
