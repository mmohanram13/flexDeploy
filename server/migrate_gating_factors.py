"""
Migration script to update database schema for default gating factors
This script:
1. Backs up the existing database
2. Creates new tables for default and deployment gating factors
3. Migrates existing ring gating factors to default gating factors
4. Removes gating factor columns from rings table
"""
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime


def backup_database(db_path: str):
    """Create a backup of the existing database"""
    backup_path = f"{db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_path)
    print(f"✓ Database backed up to: {backup_path}")
    return backup_path


def migrate_database(db_path: str = "flexdeploy.db"):
    """Run the migration"""
    if not Path(db_path).exists():
        print(f"Database not found at {db_path}")
        print("Creating fresh database with new schema...")
        from server.database import init_database
        init_database(db_path, reset=True)
        return
    
    print("Starting database migration...")
    
    # Backup first
    backup_path = backup_database(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if migration is needed
        cursor.execute("PRAGMA table_info(rings)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'avg_cpu_usage_max' not in columns:
            print("✓ Migration already completed or not needed")
            conn.close()
            return
        
        print("Creating new tables...")
        
        # Create default_gating_factors table
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
        
        # Create deployment_gating_factors table
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
        
        print("✓ New tables created")
        
        # Migrate existing ring gating factors to default gating factors
        # Take the first ring's gating factors as default (Ring 0 - Canary)
        cursor.execute("""
            SELECT avg_cpu_usage_max, avg_memory_usage_max, avg_disk_free_space_min,
                   risk_score_min, risk_score_max
            FROM rings
            WHERE ring_id = 0
        """)
        
        ring_0_data = cursor.fetchone()
        if ring_0_data:
            cursor.execute("""
                INSERT INTO default_gating_factors 
                (avg_cpu_usage_max, avg_memory_usage_max, avg_disk_free_space_min,
                 risk_score_min, risk_score_max)
                VALUES (?, ?, ?, ?, ?)
            """, ring_0_data)
            print("✓ Default gating factors set from Ring 0")
        else:
            # Insert sensible defaults if no data exists
            cursor.execute("""
                INSERT INTO default_gating_factors 
                (avg_cpu_usage_max, avg_memory_usage_max, avg_disk_free_space_min,
                 risk_score_min, risk_score_max)
                VALUES (100, 100, 0, 0, 100)
            """)
            print("✓ Default gating factors set to defaults")
        
        # Copy default gating factors to all existing deployments
        cursor.execute("SELECT deployment_id FROM deployments")
        deployments = cursor.fetchall()
        
        default_gating = cursor.execute("""
            SELECT avg_cpu_usage_max, avg_memory_usage_max, avg_disk_free_space_min,
                   risk_score_min, risk_score_max
            FROM default_gating_factors
            ORDER BY id DESC
            LIMIT 1
        """).fetchone()
        
        for (deployment_id,) in deployments:
            cursor.execute("""
                INSERT INTO deployment_gating_factors 
                (deployment_id, avg_cpu_usage_max, avg_memory_usage_max, avg_disk_free_space_min,
                 risk_score_min, risk_score_max)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (deployment_id, *default_gating))
        
        if deployments:
            print(f"✓ Copied gating factors to {len(deployments)} existing deployments")
        
        # Create new rings table without gating factor columns
        print("Migrating rings table...")
        
        cursor.execute("""
            CREATE TABLE rings_new (
                ring_id INTEGER PRIMARY KEY,
                ring_name TEXT NOT NULL,
                categorization_prompt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            INSERT INTO rings_new (ring_id, ring_name, categorization_prompt, created_at, updated_at)
            SELECT ring_id, ring_name, categorization_prompt, created_at, updated_at
            FROM rings
        """)
        
        cursor.execute("DROP TABLE rings")
        cursor.execute("ALTER TABLE rings_new RENAME TO rings")
        
        print("✓ Rings table migrated")
        
        conn.commit()
        print("\n✓ Migration completed successfully!")
        print(f"  Backup saved at: {backup_path}")
        
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        print(f"  Rolling back... restoring from backup: {backup_path}")
        conn.close()
        shutil.copy2(backup_path, db_path)
        print("  Database restored from backup")
        raise
    
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_database()
