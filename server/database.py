"""
Database models and initialization for FlexDeploy
"""
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any


class Database:
    def __init__(self, db_path: str = "flexdeploy.db"):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
    
    def connect(self):
        """Connect to the database"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
    
    def create_tables(self):
        """Create all database tables"""
        cursor = self.conn.cursor()
        
        # Devices table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                device_id TEXT PRIMARY KEY,
                device_name TEXT NOT NULL,
                manufacturer TEXT NOT NULL,
                model TEXT NOT NULL,
                os_name TEXT NOT NULL,
                site TEXT NOT NULL,
                department TEXT NOT NULL,
                ring INTEGER NOT NULL,
                total_memory TEXT NOT NULL,
                total_storage TEXT NOT NULL,
                network_speed TEXT NOT NULL,
                avg_cpu_usage REAL NOT NULL,
                avg_memory_usage REAL NOT NULL,
                avg_disk_space REAL NOT NULL,
                risk_score INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Deployments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deployments (
                deployment_id TEXT PRIMARY KEY,
                deployment_name TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('Not Started', 'In Progress', 'Completed', 'Failed', 'Stopped')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Deployment rings table (tracks ring status per deployment)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deployment_rings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deployment_id TEXT NOT NULL,
                ring_id INTEGER NOT NULL,
                ring_name TEXT NOT NULL,
                device_count INTEGER NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('Not Started', 'In Progress', 'Completed', 'Failed', 'Stopped')),
                failure_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (deployment_id) REFERENCES deployments(deployment_id),
                FOREIGN KEY (ring_id) REFERENCES rings(ring_id),
                UNIQUE(deployment_id, ring_id)
            )
        """)
        
        # Rings configuration table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rings (
                ring_id INTEGER PRIMARY KEY,
                ring_name TEXT NOT NULL,
                categorization_prompt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Default gating factors table (template for new deployments)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS default_gating_factors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                avg_cpu_usage_max REAL,
                avg_memory_usage_max REAL,
                avg_disk_free_space_min REAL,
                risk_score_min INTEGER,
                risk_score_max INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Deployment gating factors table (per deployment)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deployment_gating_factors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deployment_id TEXT NOT NULL UNIQUE,
                avg_cpu_usage_max REAL,
                avg_memory_usage_max REAL,
                avg_disk_free_space_min REAL,
                risk_score_min INTEGER,
                risk_score_max INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (deployment_id) REFERENCES deployments(deployment_id)
            )
        """)
        
        self.conn.commit()
        print("✓ Database tables created successfully")
    
    def drop_tables(self):
        """Drop all tables (for reset/testing purposes)"""
        cursor = self.conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS deployment_gating_factors")
        cursor.execute("DROP TABLE IF EXISTS deployment_rings")
        cursor.execute("DROP TABLE IF EXISTS deployments")
        cursor.execute("DROP TABLE IF EXISTS devices")
        cursor.execute("DROP TABLE IF EXISTS rings")
        cursor.execute("DROP TABLE IF EXISTS default_gating_factors")
        self.conn.commit()
        print("✓ All tables dropped")
    
    def get_dashboard_metrics(self):
        """Calculate dashboard metrics from the database"""
        cursor = self.conn.cursor()
        
        total_devices = cursor.execute("SELECT COUNT(*) as count FROM devices").fetchone()[0]
        total_deployments = cursor.execute("SELECT COUNT(*) as count FROM deployments").fetchone()[0]
        active_rings = cursor.execute("SELECT COUNT(*) as count FROM rings").fetchone()[0]
        
        return {
            "totalDevices": total_devices,
            "totalDeployments": total_deployments,
            "activeRings": active_rings
        }
    
    def get_device_distribution_by_ring(self):
        """Get device count distribution by ring"""
        cursor = self.conn.cursor()
        
        distribution = cursor.execute("""
            SELECT 
                CASE ring
                    WHEN 0 THEN 'Ring 0'
                    WHEN 1 THEN 'Ring 1'
                    WHEN 2 THEN 'Ring 2'
                    WHEN 3 THEN 'Ring 3'
                END as name,
                COUNT(*) as value
            FROM devices
            GROUP BY ring
            ORDER BY ring
        """).fetchall()
        
        return [dict(row) for row in distribution]


# Global database instance
_db_instance: Optional[Database] = None


def get_db() -> Database:
    """Get or create the global database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
        _db_instance.connect()
    return _db_instance


def get_all_devices() -> List[Dict[str, Any]]:
    """Get all devices from the database"""
    db = get_db()
    cursor = db.conn.cursor()
    
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
            "device_id": row[0],
            "device_name": row[1],
            "manufacturer": row[2],
            "model": row[3],
            "os_name": row[4],
            "site": row[5],
            "department": row[6],
            "ring": row[7],
            "total_memory": row[8],
            "total_storage": row[9],
            "network_speed": row[10],
            "avg_cpu_usage": row[11],
            "avg_memory_usage": row[12],
            "avg_disk_space": row[13],
            "risk_score": row[14],
            "created_at": row[15],
            "updated_at": row[16]
        })
    
    return devices


def get_device_by_id(device_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific device by ID"""
    db = get_db()
    cursor = db.conn.cursor()
    
    row = cursor.execute("""
        SELECT device_id, device_name, manufacturer, model, os_name, site, department, ring,
               total_memory, total_storage, network_speed, avg_cpu_usage, avg_memory_usage,
               avg_disk_space, risk_score, created_at, updated_at
        FROM devices
        WHERE device_id = ?
    """, (device_id,)).fetchone()
    
    if not row:
        return None
    
    return {
        "device_id": row[0],
        "device_name": row[1],
        "manufacturer": row[2],
        "model": row[3],
        "os_name": row[4],
        "site": row[5],
        "department": row[6],
        "ring": row[7],
        "total_memory": row[8],
        "total_storage": row[9],
        "network_speed": row[10],
        "avg_cpu_usage": row[11],
        "avg_memory_usage": row[12],
        "avg_disk_space": row[13],
        "risk_score": row[14],
        "created_at": row[15],
        "updated_at": row[16]
    }


def create_device(device_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new device in the database"""
    db = get_db()
    cursor = db.conn.cursor()
    
    cursor.execute("""
        INSERT INTO devices (
            device_id, device_name, manufacturer, model, os_name, site, department, ring,
            total_memory, total_storage, network_speed, avg_cpu_usage, avg_memory_usage,
            avg_disk_space, risk_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        device_data["device_id"],
        device_data["device_name"],
        device_data["manufacturer"],
        device_data["model"],
        device_data["os_name"],
        device_data["site"],
        device_data["department"],
        device_data["ring"],
        device_data["total_memory"],
        device_data["total_storage"],
        device_data["network_speed"],
        device_data["avg_cpu_usage"],
        device_data["avg_memory_usage"],
        device_data["avg_disk_space"],
        device_data["risk_score"]
    ))
    
    db.conn.commit()
    return get_device_by_id(device_data["device_id"])


def update_device(device_id: str, device_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update an existing device"""
    db = get_db()
    cursor = db.conn.cursor()
    
    cursor.execute("""
        UPDATE devices
        SET device_name = ?, manufacturer = ?, model = ?, os_name = ?, site = ?,
            department = ?, ring = ?, total_memory = ?, total_storage = ?,
            network_speed = ?, avg_cpu_usage = ?, avg_memory_usage = ?,
            avg_disk_space = ?, risk_score = ?, updated_at = CURRENT_TIMESTAMP
        WHERE device_id = ?
    """, (
        device_data["device_name"],
        device_data["manufacturer"],
        device_data["model"],
        device_data["os_name"],
        device_data["site"],
        device_data["department"],
        device_data["ring"],
        device_data["total_memory"],
        device_data["total_storage"],
        device_data["network_speed"],
        device_data["avg_cpu_usage"],
        device_data["avg_memory_usage"],
        device_data["avg_disk_space"],
        device_data["risk_score"],
        device_id
    ))
    
    db.conn.commit()
    return get_device_by_id(device_id)


def get_ring_configurations() -> List[Dict[str, Any]]:
    """Get all ring configurations"""
    db = get_db()
    cursor = db.conn.cursor()
    
    rows = cursor.execute("""
        SELECT ring_id, ring_name, categorization_prompt, created_at, updated_at
        FROM rings
        ORDER BY ring_id
    """).fetchall()
    
    rings = []
    for row in rows:
        rings.append({
            "ring_id": row[0],
            "ring_name": row[1],
            "categorization_prompt": row[2],
            "created_at": row[3],
            "updated_at": row[4]
        })
    
    return rings


def get_deployment_status(deployment_id: str) -> Optional[Dict[str, Any]]:
    """Get deployment status including ring details"""
    db = get_db()
    cursor = db.conn.cursor()
    
    # Get deployment info
    deployment = cursor.execute("""
        SELECT deployment_id, deployment_name, status, created_at, updated_at
        FROM deployments
        WHERE deployment_id = ?
    """, (deployment_id,)).fetchone()
    
    if not deployment:
        return None
    
    # Get ring statuses for this deployment
    rings = cursor.execute("""
        SELECT ring_id, ring_name, device_count, status, failure_reason
        FROM deployment_rings
        WHERE deployment_id = ?
        ORDER BY ring_id
    """, (deployment_id,)).fetchall()
    
    ring_list = []
    for ring in rings:
        ring_list.append({
            "ring_id": ring[0],
            "ring_name": ring[1],
            "device_count": ring[2],
            "status": ring[3],
            "failure_reason": ring[4]
        })
    
    return {
        "deployment_id": deployment[0],
        "deployment_name": deployment[1],
        "status": deployment[2],
        "created_at": deployment[3],
        "updated_at": deployment[4],
        "rings": ring_list
    }


def get_all_deployments() -> List[Dict[str, Any]]:
    """Get all deployments"""
    db = get_db()
    cursor = db.conn.cursor()
    
    rows = cursor.execute("""
        SELECT deployment_id, deployment_name, status, created_at, updated_at
        FROM deployments
        ORDER BY created_at DESC
    """).fetchall()
    
    deployments = []
    for row in rows:
        deployments.append({
            "deployment_id": row[0],
            "deployment_name": row[1],
            "status": row[2],
            "created_at": row[3],
            "updated_at": row[4]
        })
    
    return deployments


def init_database(db_path: str = "flexdeploy.db", reset: bool = False):
    """Initialize the database"""
    db = Database(db_path)
    db.connect()
    
    if reset:
        db.drop_tables()
    
    db.create_tables()
    
    # Set the global instance
    global _db_instance
    _db_instance = db
    
    return db


# Export list for module imports
__all__ = [
    'Database',
    'init_database',
    'get_db',
    'get_all_devices',
    'get_device_by_id',
    'create_device',
    'update_device',
    'get_ring_configurations',
    'get_deployment_status',
    'get_all_deployments'
]


if __name__ == "__main__":
    # Initialize database
    db = init_database(reset=True)
    print("Database initialized successfully!")
    db.close()
