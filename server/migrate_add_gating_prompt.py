"""
Migration script to add gating_prompt column to deployment_gating_factors table
Run this once to update existing databases
"""
import sqlite3
import os

def migrate():
    # Get database path
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "flexdeploy.db")
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        print("No migration needed - fresh database will have the column")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(deployment_gating_factors)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'gating_prompt' in columns:
            print("[OK] gating_prompt column already exists")
            return
        
        # Add the column
        print("[INFO] Adding gating_prompt column to deployment_gating_factors table...")
        cursor.execute("""
            ALTER TABLE deployment_gating_factors
            ADD COLUMN gating_prompt TEXT
        """)
        
        conn.commit()
        print("[OK] Migration completed successfully")
        print("     gating_prompt column added to deployment_gating_factors table")
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
