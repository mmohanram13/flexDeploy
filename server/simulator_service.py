"""
Simulator Service Module
Handles all simulation-related business logic and operations.
"""
from typing import Optional, List, Dict, Any
import sqlite3


class SimulatorService:
    """Service class for simulator operations"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        self.conn = db_connection
    
    def create_or_update_device(
        self,
        device_id: str,
        device_name: str,
        manufacturer: str,
        model: str,
        os_name: str,
        site: str,
        department: str,
        ring: int,
        total_memory: str,
        total_storage: str,
        network_speed: str,
        avg_cpu_usage: float,
        avg_memory_usage: float,
        avg_disk_space: float,
        risk_score: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create or update a device with metadata.
        
        Returns:
            Dict with status, deviceId, and calculated riskScore
        """
        cursor = self.conn.cursor()
        
        # Calculate risk score if not provided
        if risk_score is None:
            risk_score = self._calculate_risk_score(
                avg_cpu_usage, avg_memory_usage, avg_disk_space
            )
        
        cursor.execute("""
            INSERT INTO devices (
                device_id, device_name, manufacturer, model, os_name, site, department,
                ring, total_memory, total_storage, network_speed, avg_cpu_usage,
                avg_memory_usage, avg_disk_space, risk_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(device_id) DO UPDATE SET
                device_name = excluded.device_name,
                manufacturer = excluded.manufacturer,
                model = excluded.model,
                os_name = excluded.os_name,
                site = excluded.site,
                department = excluded.department,
                ring = excluded.ring,
                total_memory = excluded.total_memory,
                total_storage = excluded.total_storage,
                network_speed = excluded.network_speed,
                avg_cpu_usage = excluded.avg_cpu_usage,
                avg_memory_usage = excluded.avg_memory_usage,
                avg_disk_space = excluded.avg_disk_space,
                risk_score = excluded.risk_score,
                updated_at = CURRENT_TIMESTAMP
        """, (
            device_id, device_name, manufacturer, model, os_name, site, department,
            ring, total_memory, total_storage, network_speed, avg_cpu_usage,
            avg_memory_usage, avg_disk_space, risk_score
        ))
        
        self.conn.commit()
        
        return {
            "status": "success",
            "deviceId": device_id,
            "riskScore": risk_score
        }
    
    def update_device_metrics(
        self,
        device_id: str,
        avg_cpu_usage: float,
        avg_memory_usage: float,
        avg_disk_space: float,
        risk_score: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update metrics for a specific device.
        
        Returns:
            Dict with status, deviceId, and calculated riskScore
        """
        cursor = self.conn.cursor()
        
        # Calculate risk score if not provided
        if risk_score is None:
            risk_score = self._calculate_risk_score(
                avg_cpu_usage, avg_memory_usage, avg_disk_space
            )
        
        cursor.execute("""
            UPDATE devices
            SET avg_cpu_usage = ?,
                avg_memory_usage = ?,
                avg_disk_space = ?,
                risk_score = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE device_id = ?
        """, (avg_cpu_usage, avg_memory_usage, avg_disk_space, risk_score, device_id))
        
        if cursor.rowcount == 0:
            return {"status": "error", "message": "Device not found"}
        
        self.conn.commit()
        
        return {
            "status": "success",
            "deviceId": device_id,
            "riskScore": risk_score
        }
    
    def update_ring_metrics(
        self,
        ring_id: int,
        deployment_id: str,
        avg_cpu_usage: Optional[float] = None,
        avg_memory_usage: Optional[float] = None,
        avg_disk_space: Optional[float] = None,
        risk_score: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update metrics for all devices in a ring.
        
        Returns:
            Dict with status, ringId, and devicesUpdated count
        """
        cursor = self.conn.cursor()
        
        # Get all devices in the ring
        devices = cursor.execute("""
            SELECT device_id
            FROM devices
            WHERE ring = ?
        """, (ring_id,)).fetchall()
        
        if not devices:
            return {
                "status": "error",
                "message": f"No devices found in ring {ring_id}"
            }
        
        updated_count = 0
        for device in devices:
            device_id = device[0]
            
            # Update individual metrics if provided
            if avg_cpu_usage is not None:
                cursor.execute("""
                    UPDATE devices SET avg_cpu_usage = ? WHERE device_id = ?
                """, (avg_cpu_usage, device_id))
            
            if avg_memory_usage is not None:
                cursor.execute("""
                    UPDATE devices SET avg_memory_usage = ? WHERE device_id = ?
                """, (avg_memory_usage, device_id))
            
            if avg_disk_space is not None:
                cursor.execute("""
                    UPDATE devices SET avg_disk_space = ? WHERE device_id = ?
                """, (avg_disk_space, device_id))
            
            # Recalculate risk score if metrics changed
            if any([avg_cpu_usage, avg_memory_usage, avg_disk_space]):
                device_data = cursor.execute("""
                    SELECT avg_cpu_usage, avg_memory_usage, avg_disk_space
                    FROM devices WHERE device_id = ?
                """, (device_id,)).fetchone()
                
                new_risk_score = self._calculate_risk_score(
                    device_data[0], device_data[1], device_data[2]
                )
                
                cursor.execute("""
                    UPDATE devices
                    SET risk_score = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE device_id = ?
                """, (new_risk_score, device_id))
            
            updated_count += 1
        
        self.conn.commit()
        
        return {
            "status": "success",
            "ringId": ring_id,
            "devicesUpdated": updated_count
        }
    
    def update_deployment_ring_status(
        self,
        deployment_id: str,
        ring_id: int,
        status: str,
        failure_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update the status of a ring in a deployment.
        
        Returns:
            Dict with status, deploymentId, ringId, and newStatus
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            UPDATE deployment_rings
            SET status = ?,
                failure_reason = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE deployment_id = ? AND ring_id = ?
        """, (status, failure_reason, deployment_id, ring_id))
        
        if cursor.rowcount == 0:
            return {
                "status": "error",
                "message": f"Deployment ring not found: {deployment_id}, Ring {ring_id}"
            }
        
        self.conn.commit()
        
        return {
            "status": "success",
            "deploymentId": deployment_id,
            "ringId": ring_id,
            "newStatus": status
        }
    
    def get_ring_devices(self, deployment_id: str, ring_id: int) -> List[Dict[str, Any]]:
        """
        Get all devices in a specific ring.
        
        Returns:
            List of device dictionaries
        """
        cursor = self.conn.cursor()
        
        devices = cursor.execute("""
            SELECT device_id, device_name, manufacturer, model, os_name, site, department,
                   ring, total_memory, total_storage, network_speed, avg_cpu_usage,
                   avg_memory_usage, avg_disk_space, risk_score
            FROM devices
            WHERE ring = ?
            ORDER BY device_id
        """, (ring_id,)).fetchall()
        
        device_list = []
        for row in devices:
            device_list.append({
                "deviceId": row[0],
                "deviceName": row[1],
                "manufacturer": row[2],
                "model": row[3],
                "osName": row[4],
                "site": row[5],
                "department": row[6],
                "ring": row[7],
                "totalMemory": row[8],
                "totalStorage": row[9],
                "networkSpeed": row[10],
                "avgCpuUsage": row[11],
                "avgMemoryUsage": row[12],
                "avgDiskSpace": row[13],
                "riskScore": row[14],
            })
        
        return device_list
    
    def get_stress_profile(self, level: str) -> Dict[str, float]:
        """
        Get pre-configured stress profile.
        
        Args:
            level: 'low', 'normal', 'high', or 'critical'
        
        Returns:
            Dict with cpu, memory, and disk values
        """
        stress_profiles = {
            "low": {"cpu": 25.0, "memory": 30.0, "disk": 20.0},
            "normal": {"cpu": 50.0, "memory": 55.0, "disk": 45.0},
            "high": {"cpu": 75.0, "memory": 80.0, "disk": 70.0},
            "critical": {"cpu": 95.0, "memory": 92.0, "disk": 88.0},
        }
        return stress_profiles.get(level, stress_profiles["normal"])
    
    def apply_stress_profile(
        self,
        deployment_id: str,
        ring_id: int,
        stress_level: str
    ) -> Dict[str, Any]:
        """
        Apply a pre-configured stress profile to a ring.
        
        Returns:
            Dict with status and profile information
        """
        profile = self.get_stress_profile(stress_level)
        
        result = self.update_ring_metrics(
            ring_id=ring_id,
            deployment_id=deployment_id,
            avg_cpu_usage=profile["cpu"],
            avg_memory_usage=profile["memory"],
            avg_disk_space=profile["disk"]
        )
        
        if result["status"] == "success":
            result["stressLevel"] = stress_level
            result["profile"] = profile
        
        return result
    
    @staticmethod
    def _calculate_risk_score(
        avg_cpu_usage: float,
        avg_memory_usage: float,
        avg_disk_space: float
    ) -> int:
        """
        Calculate risk score based on resource usage.
        
        Formula:
        - avg_usage = (CPU + Memory + (100 - Disk)) / 3
        - >80% usage  → Risk 0-30   (High Risk)
        - >50% usage  → Risk 31-70  (Medium Risk)
        - ≤50% usage  → Risk 71-100 (Low Risk)
        
        Returns:
            Risk score (0-100)
        """
        avg_usage = (avg_cpu_usage + avg_memory_usage + (100 - avg_disk_space)) / 3
        
        if avg_usage > 80:
            risk_score = int(30 - (avg_usage - 80) * 1.5)
        elif avg_usage > 50:
            risk_score = int(70 - (avg_usage - 50))
        else:
            risk_score = int(71 + (50 - avg_usage) * 0.58)
        
        return max(0, min(100, risk_score))
