"""Database configuration and direct SQLite connection handling."""

import sqlite3
import os
import asyncio
from typing import List, Dict, Any, Optional
from threading import Lock

# Database path relative to simulator
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'server', 'flexdeploy.db'))
DB_AVAILABLE = False

# Database lock for thread-safe operations
_db_lock = Lock()
_connection_timeout = 30.0  # 30 seconds timeout


def check_database_availability():
    """Check if database file exists and is accessible."""
    global DB_AVAILABLE
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.close()
            DB_AVAILABLE = True
            print(f"[Config] Database connection successful: {DB_PATH}")
        except Exception as e:
            print(f"[Config] Database connection failed: {e}")
            DB_AVAILABLE = False
    else:
        print(f"[Config] Database file not found: {DB_PATH}")
        DB_AVAILABLE = False


def get_db_connection():
    """Get a database connection with timeout and WAL mode."""
    if not DB_AVAILABLE:
        raise Exception("Database not available")
    
    conn = sqlite3.connect(DB_PATH, timeout=_connection_timeout, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    
    # Enable WAL mode for better concurrent access
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")  # 30 second busy timeout
    
    return conn


def get_all_devices() -> List[Dict[str, Any]]:
    """Get all devices from the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        rows = cursor.execute("""
            SELECT device_id, device_name, manufacturer, model, os_name, site, department, ring,
                   total_memory, total_storage, network_speed, avg_cpu_usage, avg_memory_usage,
                   avg_disk_space, risk_score, created_at, updated_at
            FROM devices
            ORDER BY device_id
        """).fetchall()
        
        devices = []
        for row in rows:
            devices.append({
                "device_id": row["device_id"],
                "device_name": row["device_name"],
                "manufacturer": row["manufacturer"],
                "model": row["model"],
                "os_name": row["os_name"],
                "site": row["site"],
                "department": row["department"],
                "ring": row["ring"],
                "total_memory": row["total_memory"],
                "total_storage": row["total_storage"],
                "network_speed": row["network_speed"],
                "avg_cpu_usage": row["avg_cpu_usage"],
                "avg_memory_usage": row["avg_memory_usage"],
                "avg_disk_space": row["avg_disk_space"],
                "risk_score": row["risk_score"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })
        
        conn.close()
        return devices
    except Exception as e:
        print(f"[Config] Error fetching devices: {e}")
        return []


def get_device_by_id(device_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific device by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        row = cursor.execute("""
            SELECT device_id, device_name, manufacturer, model, os_name, site, department, ring,
                   total_memory, total_storage, network_speed, avg_cpu_usage, avg_memory_usage,
                   avg_disk_space, risk_score, created_at, updated_at
            FROM devices
            WHERE device_id = ?
        """, (device_id,)).fetchone()
        
        conn.close()
        
        if not row:
            return None
        
        return {
            "device_id": row["device_id"],
            "device_name": row["device_name"],
            "manufacturer": row["manufacturer"],
            "model": row["model"],
            "os_name": row["os_name"],
            "site": row["site"],
            "department": row["department"],
            "ring": row["ring"],
            "total_memory": row["total_memory"],
            "total_storage": row["total_storage"],
            "network_speed": row["network_speed"],
            "avg_cpu_usage": row["avg_cpu_usage"],
            "avg_memory_usage": row["avg_memory_usage"],
            "avg_disk_space": row["avg_disk_space"],
            "risk_score": row["risk_score"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
    except Exception as e:
        print(f"[Config] Error fetching device {device_id}: {e}")
        return None


def get_ring_configurations() -> List[Dict[str, Any]]:
    """Get all ring configurations."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        rows = cursor.execute("""
            SELECT ring_id, ring_name, categorization_prompt, created_at, updated_at
            FROM rings
            ORDER BY ring_id
        """).fetchall()
        
        rings = []
        for row in rows:
            rings.append({
                "ring_id": row["ring_id"],
                "ring_name": row["ring_name"],
                "categorization_prompt": row["categorization_prompt"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            })
        
        conn.close()
        return rings
    except Exception as e:
        print(f"[Config] Error fetching ring configurations: {e}")
        return []


def update_device_attributes(device_id: str, cpu_usage: float, memory_usage: float, 
                            disk_usage: float, risk_score: int):
    """Update device attributes in database with lock."""
    with _db_lock:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE devices 
                SET avg_cpu_usage = ?, 
                    avg_memory_usage = ?, 
                    avg_disk_space = ?, 
                    risk_score = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE device_id = ?
            """, (cpu_usage, memory_usage, disk_usage, risk_score, device_id))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.OperationalError as e:
            if "locked" in str(e):
                print(f"[Config] Database locked, retrying update for device {device_id}")
                # Retry once after a short delay
                import time
                time.sleep(0.1)
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE devices 
                        SET avg_cpu_usage = ?, 
                            avg_memory_usage = ?, 
                            avg_disk_space = ?, 
                            risk_score = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE device_id = ?
                    """, (cpu_usage, memory_usage, disk_usage, risk_score, device_id))
                    conn.commit()
                    conn.close()
                    return True
                except Exception:
                    pass
            print(f"[Config] Error updating device {device_id}: {e}")
            return False
        except Exception as e:
            print(f"[Config] Error updating device {device_id}: {e}")
            return False


def update_device_ring(device_id: str, ring_id: int):
    """Update device ring assignment in database with lock."""
    with _db_lock:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE devices 
                SET ring = ?, updated_at = CURRENT_TIMESTAMP
                WHERE device_id = ?
            """, (ring_id, device_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[Config] Error updating device ring: {e}")
            return False


def ensure_demo_deployments():
    """Ensure demo deployments exist in database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        demo_deployments = [
            ("DEP-001", "Security Patch Deployment", "Completed"),
            ("DEP-002", "Application Update v2.1", "Completed"),
            ("DEP-003", "OS Update Rollout", "In Progress"),
            ("DEP-004", "Critical Security Update", "Failed")
        ]
        
        for dep_id, dep_name, status in demo_deployments:
            cursor.execute("""
                INSERT OR REPLACE INTO deployments (deployment_id, deployment_name, status, created_at, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (dep_id, dep_name, status))
        
        conn.commit()
        conn.close()
        print("[Config] Demo deployments initialized")
        return True
    except Exception as e:
        print(f"[Config] Error ensuring demo deployments: {e}")
        return False


# Initialize on import
check_database_availability()
