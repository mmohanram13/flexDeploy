"""Device management and status tracking."""

import asyncio
import logging
import random
from datetime import datetime
from typing import Dict, List

from .config_loader import (
    DB_AVAILABLE, 
    get_all_devices, 
    update_device_attributes, 
    update_device_ring
)
from ..common import DeviceStatus, RingType, TaskStatus

logger = logging.getLogger(__name__)


class DeviceManager:
    """Manages device status and metrics."""
    
    def __init__(self, config):
        self.config = config
        self.device_statuses: Dict[str, DeviceStatus] = {}
        self.device_cache: Dict[str, dict] = {}
        self.attribute_alteration_interval = 15.0
    
    def create_device_status(self, slave_id: str, capabilities: dict, device_status_dict: dict = None) -> DeviceStatus:
        """Create device status from capabilities."""
        if not device_status_dict:
            battery_level = capabilities.get("battery", random.randint(40, 95))
            cpu_usage = capabilities.get("cpu", random.uniform(5.0, 25.0)) * 10
            
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
        
        try:
            device_status = DeviceStatus.from_dict(device_status_dict)
            self.device_statuses[slave_id] = device_status
            return device_status
        except Exception as e:
            logger.error(f"Failed to parse device status: {e}")
            device_status = DeviceStatus(
                slave_id=slave_id,
                battery_level=capabilities.get("battery", 75),
                battery_charging=random.choice([True, False]),
                cpu_usage=capabilities.get("cpu", 10.0) * 10,
                memory_usage=random.uniform(20.0, 50.0),
                disk_usage=random.uniform(30.0, 70.0),
                device_name=f"Agent-{slave_id[-6:]}"
            )
            self.device_statuses[slave_id] = device_status
            return device_status
    
    def calculate_device_risk_score(self, device_status: DeviceStatus) -> int:
        """Calculate risk score using linear interpolation."""
        avg_usage = (device_status.cpu_usage + device_status.memory_usage + device_status.disk_usage) / 3.0
        
        if avg_usage > 80.0:
            risk_score = int(30 * (1 - (avg_usage - 80) / 20))
            return max(0, min(30, risk_score))
        elif avg_usage > 50.0:
            risk_score = int(31 + 39 * (1 - (avg_usage - 50) / 30))
            return max(31, min(70, risk_score))
        else:
            risk_score = int(71 + 29 * (1 - avg_usage / 50))
            return max(71, min(100, risk_score))
    
    async def load_devices_from_db(self):
        """Load devices from database."""
        if DB_AVAILABLE:
            try:
                devices = get_all_devices()
                if devices:
                    logger.info(f"Fetched {len(devices)} devices from database")
                else:
                    logger.warning("No devices found in database, using fallback")
                    devices = self._get_fallback_devices()
            except Exception as e:
                logger.error(f"Error fetching devices: {e}")
                devices = self._get_fallback_devices()
        else:
            logger.warning("Database not available, using fallback devices")
            devices = self._get_fallback_devices()
        
        self.device_cache = {device["device_id"]: device for device in devices}
        logger.info(f"Loaded {len(devices)} devices into cache")
    
    def _get_fallback_devices(self) -> List[dict]:
        """Generate fallback devices."""
        return [
            {
                "device_id": f"DEV-{i:04d}",
                "device_name": f"Device-{i}",
                "manufacturer": random.choice(["Dell", "HP", "Lenovo", "Apple"]),
                "model": f"Model-{random.randint(1000, 9999)}",
                "os_name": random.choice(["Windows 11", "macOS", "Ubuntu"]),
                "site": random.choice(["HQ", "Branch-A", "Branch-B"]),
                "department": random.choice(["IT", "Finance", "HR"]),
                "ring": random.randint(0, 3),
                "total_memory": f"{random.randint(8, 64)} GB",
                "total_storage": f"{random.randint(256, 2048)} GB",
                "network_speed": f"{random.randint(100, 1000)} Mbps",
                "avg_cpu_usage": random.uniform(10.0, 80.0),
                "avg_memory_usage": random.uniform(20.0, 70.0),
                "avg_disk_space": random.uniform(30.0, 90.0),
                "risk_score": random.randint(0, 100)
            }
            for i in range(10)
        ]
    
    async def attribute_alteration_loop(self, get_running_state):
        """Continuously alter device attributes."""
        logger.info("Starting device attribute alteration loop")
        
        while True:
            is_running = get_running_state() if callable(get_running_state) else get_running_state
            if not is_running:
                break
                
            try:
                await self._randomly_alter_attributes()
                await asyncio.sleep(self.attribute_alteration_interval)
            except Exception as e:
                logger.error(f"Error in attribute alteration: {e}")
                await asyncio.sleep(self.attribute_alteration_interval)
    
    async def _randomly_alter_attributes(self):
        """Randomly alter device attributes."""
        if not self.device_statuses:
            return
        
        change_percentage = random.uniform(0.2, 0.4)
        devices_to_change = random.sample(
            list(self.device_statuses.keys()),
            int(len(self.device_statuses) * change_percentage)
        )
        
        for agent_id in devices_to_change:
            self._apply_random_scenario(agent_id)
    
    def _apply_random_scenario(self, agent_id: str):
        """Apply random performance scenario to device."""
        if agent_id not in self.device_statuses:
            return
        
        device_status = self.device_statuses[agent_id]
        scenario = random.choice([
            "performance_boost", "performance_degradation",
            "battery_drain", "battery_recovery", "high_usage_spike"
        ])
        
        if scenario == "performance_boost":
            device_status.cpu_usage = max(5.0, device_status.cpu_usage - random.uniform(10.0, 25.0))
            device_status.memory_usage = max(10.0, device_status.memory_usage - random.uniform(5.0, 15.0))
        elif scenario == "performance_degradation":
            device_status.cpu_usage = min(90.0, device_status.cpu_usage + random.uniform(15.0, 35.0))
            device_status.memory_usage = min(85.0, device_status.memory_usage + random.uniform(10.0, 25.0))
        elif scenario == "battery_drain":
            if not device_status.battery_charging:
                device_status.battery_level = max(5.0, device_status.battery_level - random.uniform(10.0, 30.0))
        
        device_status.last_updated = datetime.now()
        logger.debug(f"Applied {scenario} to {agent_id}")
    
    def get_cluster_status(self, slaves: dict, tasks: dict, ring_assignments: dict) -> dict:
        """Get overall cluster status."""
        return {
            "total_slaves": len(slaves),
            "active_slaves": len([s for s in slaves.values() if s["status"] == "busy"]),
            "idle_slaves": len([s for s in slaves.values() if s["status"] == "idle"]),
            "healthy_devices": len([d for d in self.device_statuses.values() if d.is_healthy()]),
            "total_tasks": len(tasks),
            "pending_tasks": len([t for t in tasks.values() if t.status == TaskStatus.PENDING]),
            "completed_tasks": len([t for t in tasks.values() if t.status == TaskStatus.COMPLETED]),
            "ring_distribution": {ring.value: len(devices) for ring, devices in ring_assignments.items()}
        }
