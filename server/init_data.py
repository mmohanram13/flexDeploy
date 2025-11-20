"""
Centralized data initialization for FlexDeploy
Consolidates all default/seed data in one place
"""
from typing import List, Tuple


# Ring configuration data
RINGS: List[Tuple[int, str, str]] = [
    (
        0,
        'Ring 0 - Canary (Test Bed)',
        'Test devices for initial validation. Non-production systems only.'
    ),
    (
        1,
        'Ring 1 - Low Risk Devices',
        'Devices with stable configurations, recent successful deployment history, '
        'low risk scores (71-100), standard configurations, non-executive users.'
    ),
    (
        2,
        'Ring 2 - High Risk Devices',
        'Business-critical devices with moderate to high resource usage, '
        'risk scores (31-70), mixed configurations, production systems.'
    ),
    (
        3,
        'Ring 3 - VIP Devices',
        'Executive and leadership devices, highest stability requirements, '
        'risk scores (0-30 indicating high resource usage), critical systems. '
        'Deploy only after all other rings successful.'
    ),
]


# Default gating factors (allows all devices to pass by default)
DEFAULT_GATING_FACTORS = {
    'avg_cpu_usage_max': 60.0,
    'avg_memory_usage_max': 60.0,
    'avg_disk_free_space_min': 5.0,
    'risk_score_min': 0,
    'risk_score_max': 75,
}


def populate_rings(db):
    """Populate ring configuration data"""
    cursor = db.conn.cursor()
    
    # Check if rings already exist
    ring_count = cursor.execute("SELECT COUNT(*) FROM rings").fetchone()[0]
    
    if ring_count == 0:
        print("[INFO] Populating default rings...")
        for ring in RINGS:
            cursor.execute("""
                INSERT INTO rings (ring_id, ring_name, categorization_prompt)
                VALUES (?, ?, ?)
            """, ring)
        
        db.conn.commit()
        print(f"[OK] Created {len(RINGS)} default rings")
    else:
        print(f"[INFO] Rings already exist ({ring_count}), skipping...")


def populate_default_gating_factors(db):
    """Populate default gating factors"""
    cursor = db.conn.cursor()
    
    # Check if default gating factors exist
    gating_count = cursor.execute("SELECT COUNT(*) FROM default_gating_factors").fetchone()[0]
    
    if gating_count == 0:
        print("[INFO] Populating default gating factors...")
        cursor.execute("""
            INSERT INTO default_gating_factors (
                avg_cpu_usage_max, avg_memory_usage_max, avg_disk_free_space_min,
                risk_score_min, risk_score_max
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            DEFAULT_GATING_FACTORS['avg_cpu_usage_max'],
            DEFAULT_GATING_FACTORS['avg_memory_usage_max'],
            DEFAULT_GATING_FACTORS['avg_disk_free_space_min'],
            DEFAULT_GATING_FACTORS['risk_score_min'],
            DEFAULT_GATING_FACTORS['risk_score_max']
        ))
        
        db.conn.commit()
        print("[OK] Created default gating factors")
    else:
        print(f"[INFO] Default gating factors already exist, skipping...")


def populate_all_defaults(db):
    """
    Populate all default/seed data
    This is the main entry point for initializing default data
    """
    populate_rings(db)
    populate_default_gating_factors(db)


def get_migration_summary(db):
    """Get a summary of the current database state"""
    cursor = db.conn.cursor()
    
    return {
        'rings': cursor.execute("SELECT COUNT(*) FROM rings").fetchone()[0],
        'default_gating_factors': cursor.execute("SELECT COUNT(*) FROM default_gating_factors").fetchone()[0],
        'devices': cursor.execute("SELECT COUNT(*) FROM devices").fetchone()[0],
        'deployments': cursor.execute("SELECT COUNT(*) FROM deployments").fetchone()[0],
    }


# Export constants for use in other modules
__all__ = [
    'RINGS',
    'DEFAULT_GATING_FACTORS',
    'populate_rings',
    'populate_default_gating_factors',
    'populate_all_defaults',
    'get_migration_summary',
]
