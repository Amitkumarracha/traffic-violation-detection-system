"""
Database Layer - SQLAlchemy ORM with SQLite/PostgreSQL Support

Modules:
    - models.py: SQLAlchemy models (Violation, FraudCheck, SyncLog)
    - connection.py: Database connection management and initialization
    - crud.py: Create, Read, Update operations

Usage:
    from backend.database.connection import get_db_context, startup, shutdown
    from backend.database.crud import save_violation, get_violations
    
    # Startup
    startup()
    
    # Use database
    with get_db_context() as db:
        violation = save_violation(db, violation_data)
        violations = get_violations(db, limit=50)
    
    # Shutdown
    shutdown()

Configuration:
    - Local: SQLite at ~/traffic_violation_detection/data/violations.db
    - Cloud: PostgreSQL via DATABASE_URL environment variable
    
    Environment Variable:
        DATABASE_URL=postgresql://user:password@host:5432/violations_db

Models:
    - Violation: Individual detected violations (~13 fields)
    - FraudCheck: Fraud investigation claims (~9 fields)
    - SyncLog: Synchronization tracking (~5 fields)

CRUD Functions:
    Violations:
        - save_violation(db, violation_data)
        - get_violations(db, skip, limit)
        - get_violations_by_type(db, violation_type)
        - get_violations_by_plate(db, plate_number)
        - get_violations_near_location(db, lat, lng, radius_km)
        - get_unsynced_violations(db, limit)
        - mark_synced(db, violation_id)
        - get_violation_stats(db, hours)
    
    Fraud Checks:
        - save_fraud_check(db, fraud_data)
        - get_fraud_checks(db, skip, limit)
        - get_high_fraud_checks(db, threshold)
    
    Sync Logs:
        - log_sync_attempt(db, violation_id, status, error_message)
        - get_sync_logs(db, violation_id)
    
    Utilities:
        - delete_old_violations(db, days)
        - get_total_count(db)
        - get_plate_statistics(db)

Performance:
    - SQLite: Good for < 100k violations, single device
    - PostgreSQL: For distributed deployment, 1M+ violations
    - Indexes: On timestamp, violation_type, plate_number, location, synced_to_cloud
    - Connection pooling: 10 connections (PostgreSQL)
"""

from backend.database.models import Violation, FraudCheck, SyncLog, Base
from backend.database.connection import (
    get_db,
    get_db_context,
    get_connection_info,
    health_check,
    startup,
    shutdown,
    SessionLocal,
    engine,
)
from backend.database.crud import (
    save_violation,
    get_violations,
    get_violations_by_type,
    get_violations_by_plate,
    get_violations_near_location,
    get_unsynced_violations,
    mark_synced,
    get_violation_stats,
    save_fraud_check,
    get_fraud_checks,
    get_high_fraud_checks,
    log_sync_attempt,
    get_sync_logs,
    delete_old_violations,
    get_total_count,
    get_plate_statistics,
)

__all__ = [
    # Models
    'Violation',
    'FraudCheck',
    'SyncLog',
    'Base',
    
    # Connection
    'get_db',
    'get_db_context',
    'get_connection_info',
    'health_check',
    'startup',
    'shutdown',
    'SessionLocal',
    'engine',
    
    # CRUD
    'save_violation',
    'get_violations',
    'get_violations_by_type',
    'get_violations_by_plate',
    'get_violations_near_location',
    'get_unsynced_violations',
    'mark_synced',
    'get_violation_stats',
    'save_fraud_check',
    'get_fraud_checks',
    'get_high_fraud_checks',
    'log_sync_attempt',
    'get_sync_logs',
    'delete_old_violations',
    'get_total_count',
    'get_plate_statistics',
]

__version__ = '1.0.0'
