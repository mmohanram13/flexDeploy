"""Database configuration and direct SQLite connection handling."""

import sqlite3
import os
import asyncio
from typing import List, Dict, Any, Optional
from threading import Lock

# Database path relative to simulator (database is in root directory, not in server/)
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'flexdeploy.db'))
DB_AVAILABLE = False

# Database lock for thread-safe operations
_db_lock = Lock()
_connection_timeout = 30.0  # 30 seconds timeout


def check_database_availability():
    """Check if database file exists and is accessible."""
    global DB_AVAILABLE
    
    print(f"[Config] Checking database at: {DB_PATH}")
    
    if os.path.exists(DB_PATH):
        print(f"[Config] Database file exists")
        try:
            conn = sqlite3.connect(DB_PATH)
            
            # Test if deployments table exists
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='deployments'")
            result = cursor.fetchone()
            
            if result:
                print(f"[Config] 'deployments' table found")
                
                # Check for Not Started deployments
                cursor.execute("SELECT COUNT(*) FROM deployments WHERE status = 'Not Started'")
                count = cursor.fetchone()[0]
                print(f"[Config] Found {count} 'Not Started' deployments")
            else:
                print(f"[Config] WARNING: 'deployments' table not found!")
            
            conn.close()
            DB_AVAILABLE = True
            print(f"[Config] [OK] Database connection successful")
        except Exception as e:
            print(f"[Config] [ERROR] Database connection failed: {e}")
            DB_AVAILABLE = False
    else:
        print(f"[Config] [ERROR] Database file not found")
        print(f"[Config] Please run the server first to initialize the database")
        DB_AVAILABLE = False
    
    print(f"[Config] DB_AVAILABLE = {DB_AVAILABLE}")


def get_db_connection():
    """Get a database connection with timeout and WAL mode."""
    if not DB_AVAILABLE:
        raise Exception("Database not available")
    
    conn = sqlite3.connect(DB_PATH, timeout=_connection_timeout, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    
    # Enable WAL mode for better concurrent access
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")  # 30 second busy timeout
    conn.execute("PRAGMA synchronous=NORMAL")  # Balance between safety and speed
    
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
    """Update device attributes in database with improved lock handling."""
    conn = None
    max_retries = 3
    
    for retry in range(max_retries):
        try:
            # Don't use global lock - let SQLite handle it
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
            
        except Exception as e:
            if conn:
                try:
                    conn.close()
                except:
                    pass
            
            error_msg = str(e).lower()
            if 'locked' in error_msg or 'busy' in error_msg:
                if retry < max_retries - 1:
                    import time
                    wait_time = 0.1 * (retry + 1)
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"[Config] [WARN] Device {device_id} update failed after {max_retries} retries - continuing")
                    return False  # Don't crash, just return false
            else:
                print(f"[Config] Error updating device {device_id}: {e}")
                return False
    
    return False


def update_device_ring(device_id: str, ring_id: int):
    """Update device ring assignment in database with improved lock handling."""
    conn = None
    max_retries = 3
    
    for retry in range(max_retries):
        try:
            # Don't use global lock - let SQLite handle it
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
            if conn:
                try:
                    conn.close()
                except:
                    pass
            
            error_msg = str(e).lower()
            if 'locked' in error_msg or 'busy' in error_msg:
                if retry < max_retries - 1:
                    import time
                    wait_time = 0.1 * (retry + 1)
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"[Config] [WARN] Device ring update failed after {max_retries} retries")
                    return False
            else:
                print(f"[Config] Error updating device ring: {e}")
                return False
    
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


async def update_deployment_status(deployment_id: str, status: str):
    """Update deployment status asynchronously with retry."""
    print(f"[Config] update_deployment_status called: deployment_id={deployment_id}, status={status}")
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            print(f"[Config] Attempt {attempt + 1}/{max_retries} to update deployment {deployment_id}...")
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, _update_deployment_status_sync, deployment_id, status)
            
            print(f"[Config] [OK] Deployment {deployment_id} status updated to {status}")
            return True
        except Exception as e:
            print(f"[Config] [ERROR] Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
            else:
                import traceback
                print(f"[Config] [ERROR] All attempts failed:")
                traceback.print_exc()
    return False

def _update_deployment_status_sync(deployment_id: str, status: str):
    """Synchronous database update for deployment status with improved locking."""
    print(f"[Config] _update_deployment_status_sync: {deployment_id} -> {status}")
    
    conn = None
    max_retries = 3
    
    for retry in range(max_retries):
        try:
            # Don't use the global lock - let SQLite handle it with timeouts
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Verify deployment exists
            result = cursor.execute("SELECT deployment_id, status FROM deployments WHERE deployment_id = ?", 
                                   (deployment_id,)).fetchone()
            if not result:
                print(f"[Config] [ERROR] Deployment {deployment_id} not found in database!")
                if conn:
                    conn.close()
                raise Exception(f"Deployment {deployment_id} not found")
            
            print(f"[Config] Current deployment status: {result['status']}")
            
            # Update deployment
            cursor.execute("""
                UPDATE deployments 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE deployment_id = ?
            """, (status, deployment_id))
            
            rows_affected = cursor.rowcount
            print(f"[Config] Deployment update affected {rows_affected} rows")
            
            # Update all rings if completing
            if status == 'Completed':
                cursor.execute("""
                    UPDATE deployment_rings 
                    SET status = 'Completed', updated_at = CURRENT_TIMESTAMP
                    WHERE deployment_id = ? AND status != 'Failed'
                """, (deployment_id,))
                ring_rows_affected = cursor.rowcount
                print(f"[Config] Ring update affected {ring_rows_affected} rows")
            
            conn.commit()
            
            # Verify update
            verify = cursor.execute("SELECT status FROM deployments WHERE deployment_id = ?", 
                                   (deployment_id,)).fetchone()
            print(f"[Config] Verified deployment status after update: {verify['status']}")
            
            conn.close()
            print(f"[Config] [OK] Database updates committed and verified")
            return  # Success - exit function
            
        except Exception as e:
            if conn:
                try:
                    conn.close()
                except:
                    pass
            
            error_msg = str(e).lower()
            if 'locked' in error_msg or 'busy' in error_msg:
                if retry < max_retries - 1:
                    import time
                    wait_time = 0.2 * (retry + 1)  # Progressive backoff
                    print(f"[Config] [WARN] Database locked, retry {retry + 1}/{max_retries} in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"[Config] [ERROR] Database still locked after {max_retries} retries")
                    raise
            else:
                print(f"[Config] [ERROR] Non-lock error: {e}")
                raise

async def update_ring_status(deployment_id: str, ring_id: int, status: str):
    """Update ring status asynchronously."""
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _update_ring_status_sync, deployment_id, ring_id, status)
        return True
    except Exception as e:
        print(f"[Config] Error updating ring status: {e}")
        return False

def _update_ring_status_sync(deployment_id: str, ring_id: int, status: str):
    """Synchronous database update for ring status with improved locking."""
    conn = None
    max_retries = 3
    
    for retry in range(max_retries):
        try:
            # Don't use the global lock - let SQLite handle it
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE deployment_rings 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE deployment_id = ? AND ring_id = ?
            """, (status, deployment_id, ring_id))
            conn.commit()
            conn.close()
            return  # Success
            
        except Exception as e:
            if conn:
                try:
                    conn.close()
                except:
                    pass
            
            error_msg = str(e).lower()
            if 'locked' in error_msg or 'busy' in error_msg:
                if retry < max_retries - 1:
                    import time
                    wait_time = 0.2 * (retry + 1)
                    print(f"[Config] [WARN] Database locked updating ring, retry {retry + 1}/{max_retries}...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"[Config] [ERROR] Ring update failed after {max_retries} retries")
                    raise
            else:
                raise


# Initialize on import
check_database_availability()
