"""
Database models and initialization for FlexDeploy
"""
import sqlite3
from pathlib import Path
from typing import Optional


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
                risk_score_min INTEGER,
                risk_score_max INTEGER,
                avg_cpu_usage_max REAL,
                avg_memory_usage_max REAL,
                avg_disk_free_space_min REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
        print("✓ Database tables created successfully")
    
    def drop_tables(self):
        """Drop all tables (for reset/testing purposes)"""
        cursor = self.conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS deployment_rings")
        cursor.execute("DROP TABLE IF EXISTS deployments")
        cursor.execute("DROP TABLE IF EXISTS devices")
        cursor.execute("DROP TABLE IF EXISTS rings")
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


def init_database(db_path: str = "flexdeploy.db", reset: bool = False):
    """Initialize the database"""
    db = Database(db_path)
    db.connect()
    
    if reset:
        db.drop_tables()
    
    db.create_tables()
    
    return db


if __name__ == "__main__":
    # Initialize database
    db = init_database(reset=True)
    print("Database initialized successfully!")
    db.close()
