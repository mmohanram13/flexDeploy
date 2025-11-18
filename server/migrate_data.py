"""
Migration script to populate the database with mock data
"""
from server.database import init_database


def calculate_risk_score(avg_cpu_usage, avg_memory_usage, avg_disk_usage):
    """Calculate risk score based on usage metrics"""
    avg_usage = (avg_cpu_usage + avg_memory_usage + avg_disk_usage) / 3
    if avg_usage > 80:
        return round(30 - (avg_usage - 80) * 30 / 20)
    elif avg_usage > 50:
        return round(31 + (avg_usage - 50) * 39 / 30)
    else:
        return round(71 + (50 - avg_usage) * 29 / 50)


def migrate_devices(db):
    """Migrate device data"""
    cursor = db.conn.cursor()
    
    devices = [
        ('DEV-001', 'mmr-10180', 'OpenStack Foundation', 'OpenStack Nova', 'Windows 10 Pro', 'HQ', 'IT', 1, '8 GB', '79 GB', '1 Gbps', 10.17, 23.34, 42.69),
        ('DEV-002', 'LAPTOP-RCK72RHH', 'LENOVO', 'IdeaPad Slim 5', 'Windows 11 Home', 'Coimbatore', 'Marketing', 2, '16 GB', '512 GB', '1 Gbps', 35.8, 45.2, 31.5),
        ('DEV-003', 'EXEC-LAPTOP-01', 'Dell', 'XPS 15', 'Windows 11 Pro', 'HQ', 'Executive', 3, '32 GB', '1 TB', '1 Gbps', 15.3, 28.7, 54.8),
        ('DEV-004', 'TEST-DEV-01', 'HP', 'EliteBook 840', 'Windows 10 Pro', 'HQ', 'IT', 0, '16 GB', '256 GB', '1 Gbps', 8.5, 18.2, 57.9),
        ('DEV-005', 'SALES-WKS-15', 'Lenovo', 'ThinkPad T14', 'Windows 11 Pro', 'Coimbatore', 'Sales', 2, '16 GB', '512 GB', '1 Gbps', 42.1, 58.9, 27.7),
        ('DEV-006', 'DEV-WORKSTATION-02', 'HP', 'Z4 G4', 'Windows 10 Pro', 'HQ', 'Engineering', 1, '32 GB', '1 TB', '10 Gbps', 25.3, 35.6, 48.2),
        ('DEV-007', 'FINANCE-PC-08', 'Dell', 'OptiPlex 7090', 'Windows 11 Pro', 'HQ', 'Finance', 3, '16 GB', '512 GB', '1 Gbps', 18.9, 32.4, 62.1),
        ('DEV-008', 'HR-LAPTOP-05', 'ASUS', 'VivoBook Pro', 'Windows 11 Home', 'Bangalore', 'HR', 1, '16 GB', '512 GB', '1 Gbps', 22.7, 38.9, 55.3),
        ('DEV-009', 'TEST-DEV-02', 'HP', 'EliteBook 850', 'Windows 10 Pro', 'HQ', 'IT', 0, '16 GB', '512 GB', '1 Gbps', 12.4, 21.8, 68.9),
        ('DEV-010', 'SUPPORT-WKS-12', 'Lenovo', 'ThinkCentre M90', 'Windows 10 Pro', 'Bangalore', 'Support', 1, '8 GB', '256 GB', '1 Gbps', 28.3, 42.6, 51.2),
        ('DEV-011', 'DESIGN-MAC-03', 'Apple', 'MacBook Pro 16"', 'macOS Sonoma', 'HQ', 'Design', 2, '64 GB', '2 TB', '1 Gbps', 48.7, 62.3, 35.8),
        ('DEV-012', 'CEO-LAPTOP', 'Dell', 'XPS 17', 'Windows 11 Pro', 'HQ', 'Executive', 3, '64 GB', '2 TB', '10 Gbps', 12.1, 25.3, 72.8),
        ('DEV-013', 'MARKETING-WKS-07', 'HP', 'ZBook Studio', 'Windows 11 Pro', 'Coimbatore', 'Marketing', 2, '32 GB', '1 TB', '1 Gbps', 52.8, 68.4, 28.3),
        ('DEV-014', 'LEGAL-PC-04', 'Dell', 'Precision 3660', 'Windows 11 Pro', 'HQ', 'Legal', 3, '32 GB', '512 GB', '1 Gbps', 16.8, 29.7, 58.9),
        ('DEV-015', 'OPS-SERVER-01', 'Dell', 'PowerEdge R740', 'Windows Server 2022', 'HQ', 'Operations', 3, '128 GB', '4 TB', '10 Gbps', 82.3, 88.7, 12.4),
    ]
    
    for device in devices:
        device_id, device_name, manufacturer, model, os_name, site, department, ring, total_memory, total_storage, network_speed, avg_cpu, avg_memory, avg_disk = device
        risk_score = calculate_risk_score(avg_cpu, avg_memory, 100 - avg_disk)  # Convert disk space to usage
        
        cursor.execute("""
            INSERT INTO devices (
                device_id, device_name, manufacturer, model, os_name, site, department, ring,
                total_memory, total_storage, network_speed, avg_cpu_usage, avg_memory_usage,
                avg_disk_space, risk_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (device_id, device_name, manufacturer, model, os_name, site, department, ring,
              total_memory, total_storage, network_speed, avg_cpu, avg_memory, avg_disk, risk_score))
    
    db.conn.commit()
    print(f"[OK] Migrated {len(devices)} devices")


def migrate_rings(db):
    """Migrate ring configuration data"""
    cursor = db.conn.cursor()
    
    rings = [
        (0, 'Ring 0 - Canary (Test Bed)', 
         'Test devices for initial validation. Non-production systems only.'),
        (1, 'Ring 1 - Low Risk Devices',
         'Devices with stable configurations, recent successful deployment history, low risk scores (71-100), standard configurations, non-executive users.'),
        (2, 'Ring 2 - High Risk Devices',
         'Business-critical devices with moderate to high resource usage, risk scores (31-70), mixed configurations, production systems.'),
        (3, 'Ring 3 - VIP Devices',
         'Executive and leadership devices, highest stability requirements, risk scores (0-30 indicating high resource usage), critical systems. Deploy only after all other rings successful.'),
    ]
    
    for ring in rings:
        cursor.execute("""
            INSERT INTO rings (ring_id, ring_name, categorization_prompt)
            VALUES (?, ?, ?)
        """, ring)
    
    db.conn.commit()
    print(f"[OK] Migrated {len(rings)} rings")


def migrate_default_gating_factors(db):
    """Migrate default gating factors"""
    cursor = db.conn.cursor()
    
    # Set sensible default gating factors
    cursor.execute("""
        INSERT INTO default_gating_factors (
            avg_cpu_usage_max, avg_memory_usage_max, avg_disk_free_space_min,
            risk_score_min, risk_score_max
        ) VALUES (?, ?, ?, ?, ?)
    """, (100, 100, 0, 0, 100))
    
    db.conn.commit()
    print("[OK] Migrated default gating factors")


def migrate_deployment_gating_factors(db):
    """Migrate deployment-specific gating factors"""
    cursor = db.conn.cursor()
    
    # Get all deployments and set their gating factors
    deployments = cursor.execute("SELECT deployment_id FROM deployments").fetchall()
    
    for (deployment_id,) in deployments:
        cursor.execute("""
            INSERT INTO deployment_gating_factors (
                deployment_id, avg_cpu_usage_max, avg_memory_usage_max, 
                avg_disk_free_space_min, risk_score_min, risk_score_max
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (deployment_id, 100, 100, 0, 0, 100))
    
    db.conn.commit()
    print(f"[OK] Migrated gating factors for {len(deployments)} deployments")


def migrate_deployments(db):
    """Migrate deployment data"""
    cursor = db.conn.cursor()
    
    deployments = [
        ('DEP-001', 'Windows Security Update KB5043145', 'Not Started'),
        ('DEP-002', 'Chrome Browser Update v120', 'In Progress'),
        ('DEP-003', 'Microsoft Office 365 Update', 'Completed'),
        ('DEP-004', 'Adobe Acrobat Security Patch', 'Failed'),
    ]
    
    for deployment in deployments:
        cursor.execute("""
            INSERT INTO deployments (deployment_id, deployment_name, status)
            VALUES (?, ?, ?)
        """, deployment)
    
    db.conn.commit()
    print(f"[OK] Migrated {len(deployments)} deployments")


def migrate_deployment_rings(db):
    """Migrate deployment ring status data"""
    cursor = db.conn.cursor()
    
    deployment_rings = [
        # DEP-001
        ('DEP-001', 0, 'Ring 0 - Canary (Test Bed)', 2, 'Not Started', None),
        ('DEP-001', 1, 'Ring 1 - Low Risk Devices', 5, 'Not Started', None),
        ('DEP-001', 2, 'Ring 2 - High Risk Devices', 5, 'Not Started', None),
        ('DEP-001', 3, 'Ring 3 - VIP Devices', 3, 'Not Started', None),
        # DEP-002
        ('DEP-002', 0, 'Ring 0 - Canary (Test Bed)', 2, 'Completed', None),
        ('DEP-002', 1, 'Ring 1 - Low Risk Devices', 5, 'In Progress', None),
        ('DEP-002', 2, 'Ring 2 - High Risk Devices', 5, 'Not Started', None),
        ('DEP-002', 3, 'Ring 3 - VIP Devices', 3, 'Not Started', None),
        # DEP-003
        ('DEP-003', 0, 'Ring 0 - Canary (Test Bed)', 2, 'Completed', None),
        ('DEP-003', 1, 'Ring 1 - Low Risk Devices', 5, 'Completed', None),
        ('DEP-003', 2, 'Ring 2 - High Risk Devices', 5, 'Completed', None),
        ('DEP-003', 3, 'Ring 3 - VIP Devices', 3, 'Completed', None),
        # DEP-004
        ('DEP-004', 0, 'Ring 0 - Canary (Test Bed)', 2, 'Completed', None),
        ('DEP-004', 1, 'Ring 1 - Low Risk Devices', 5, 'Completed', None),
        ('DEP-004', 2, 'Ring 2 - High Risk Devices', 5, 'Failed', 'Installation failed on 3 out of 5 devices due to insufficient disk space. Deployment halted.'),
        ('DEP-004', 3, 'Ring 3 - VIP Devices', 3, 'Stopped', 'Deployment stopped due to Ring 2 failure.'),
    ]
    
    for dr in deployment_rings:
        cursor.execute("""
            INSERT INTO deployment_rings (
                deployment_id, ring_id, ring_name, device_count, status, failure_reason
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, dr)
    
    db.conn.commit()
    print(f"[OK] Migrated {len(deployment_rings)} deployment ring records")


def main():
    """Run the migration"""
    print("Starting database migration...")
    
    # Initialize database (reset if exists)
    db = init_database(reset=True)
    
    # Migrate all data
    migrate_rings(db)
    migrate_default_gating_factors(db)
    migrate_devices(db)
    migrate_deployments(db)
    migrate_deployment_gating_factors(db)
    migrate_deployment_rings(db)
    
    # Verify migration
    print("\nMigration Summary:")
    cursor = db.conn.cursor()
    
    device_count = cursor.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
    print(f"  Devices: {device_count}")
    
    ring_count = cursor.execute("SELECT COUNT(*) FROM rings").fetchone()[0]
    print(f"  Rings: {ring_count}")
    
    deployment_count = cursor.execute("SELECT COUNT(*) FROM deployments").fetchone()[0]
    print(f"  Deployments: {deployment_count}")
    
    deployment_ring_count = cursor.execute("SELECT COUNT(*) FROM deployment_rings").fetchone()[0]
    print(f"  Deployment Rings: {deployment_ring_count}")
    
    default_gating_count = cursor.execute("SELECT COUNT(*) FROM default_gating_factors").fetchone()[0]
    print(f"  Default Gating Factors: {default_gating_count}")
    
    deployment_gating_count = cursor.execute("SELECT COUNT(*) FROM deployment_gating_factors").fetchone()[0]
    print(f"  Deployment Gating Factors: {deployment_gating_count}")
    
    print("\n[OK] Migration completed successfully!")
    
    db.close()


if __name__ == "__main__":
    main()
