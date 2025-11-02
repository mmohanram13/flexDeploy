"""
Migration script to initialize database schema with essential configuration
Note: Device and deployment data is populated by the simulator

This script uses the centralized init_data module for all default data.
"""
from server.database import init_database
from server.init_data import populate_all_defaults, get_migration_summary


def main():
    """Run the migration"""
    print("Starting database initialization...")
    print("Using centralized init_data module for all default data\n")
    
    # Initialize database (reset if exists)
    db = init_database(reset=True)
    
    # Populate all default data using centralized module
    populate_all_defaults(db)
    
    # Verify migration
    print("\nMigration Summary:")
    summary = get_migration_summary(db)
    print(f"  Rings: {summary['rings']}")
    print(f"  Default Gating Factors: {summary['default_gating_factors']}")
    print(f"  Devices: {summary['devices']}")
    print(f"  Deployments: {summary['deployments']}")
    
    print("\n[OK] Database initialized successfully!")
    print("NOTE: Use the simulator to populate device and deployment data.")
    
    db.close()


if __name__ == "__main__":
    main()
