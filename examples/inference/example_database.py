"""
Database Integration Example - Using Database Layer with Main Pipeline

This example shows how to:
    1. Initialize database
    2. Save violations detected by pipeline
    3. Query violations
    4. Sync to cloud
    5. Generate statistics
"""

import logging
from datetime import datetime, timezone
from backend.database import (
    startup, shutdown, get_db_context,
    save_violation, get_violations, get_unsynced_violations,
    mark_synced, get_violation_stats, get_connection_info
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# EXAMPLE 1: Basic Setup
# ============================================================================

def example_1_setup():
    """Initialize database on startup"""
    logger.info("=" * 70)
    logger.info("EXAMPLE 1: Database Setup")
    logger.info("=" * 70)
    
    # Initialize database
    startup()
    
    # Check connection
    info = get_connection_info()
    logger.info(f"Database: {info['db_type']}")
    logger.info(f"URL: {info['url']}")


# ============================================================================
# EXAMPLE 2: Save Violations
# ============================================================================

def example_2_save_violations():
    """Save detected violations to database"""
    logger.info("\n" + "=" * 70)
    logger.info("EXAMPLE 2: Save Violations")
    logger.info("=" * 70)
    
    with get_db_context() as db:
        # Violation 1: Without helmet
        violation_1 = save_violation(db, {
            'violation_type': 'without_helmet',
            'confidence': 0.95,
            'plate_number': 'MH12AB1234',
            'plate_confidence': 0.87,
            'latitude': 18.5204,
            'longitude': 73.8567,
            'image_path': '/path/to/helmet_violation.jpg',
            'sha256_hash': 'abc123def456ghi789jkl',
            'srgan_used': False,
            'platform': 'laptop_cpu'
        })
        
        # Violation 2: Triple ride
        violation_2 = save_violation(db, {
            'violation_type': 'triple_ride',
            'confidence': 0.92,
            'plate_number': 'MH23CD5678',
            'plate_confidence': 0.91,
            'latitude': 18.5215,
            'longitude': 73.8580,
            'image_path': '/path/to/triple_ride.jpg',
            'sha256_hash': 'xyz789abc456def123ghi',
            'srgan_used': True,  # Plate was small, upscaled
            'platform': 'raspberry_pi'
        })
        
        logger.info(f"Saved violations: {violation_1.id}, {violation_2.id}")


# ============================================================================
# EXAMPLE 3: Query Violations
# ============================================================================

def example_3_query_violations():
    """Query violations from database"""
    logger.info("\n" + "=" * 70)
    logger.info("EXAMPLE 3: Query Violations")
    logger.info("=" * 70)
    
    with get_db_context() as db:
        # Get all violations
        all_violations = get_violations(db, limit=10)
        logger.info(f"Total violations: {len(all_violations)}")
        
        for v in all_violations:
            logger.info(
                f"  {v.timestamp} | {v.violation_type:15} | "
                f"Plate: {v.plate_number:12} | Conf: {v.confidence:.2f}"
            )


# ============================================================================
# EXAMPLE 4: Cloud Synchronization
# ============================================================================

def example_4_cloud_sync():
    """Sync unsynced violations to cloud"""
    logger.info("\n" + "=" * 70)
    logger.info("EXAMPLE 4: Cloud Synchronization")
    logger.info("=" * 70)
    
    with get_db_context() as db:
        # Get unsynced violations
        unsynced = get_unsynced_violations(db, limit=5)
        logger.info(f"Unsynced violations: {len(unsynced)}")
        
        for v in unsynced:
            try:
                # Simulate cloud sync
                logger.info(f"Syncing violation {v.id} to cloud...")
                # In real scenario: upload to cloud database
                # cloud_db.insert(v.to_dict())
                
                # Mark as synced
                if mark_synced(db, v.id):
                    logger.info(f"✓ Violation {v.id} synced and marked")
            except Exception as e:
                logger.error(f"Failed to sync violation {v.id}: {e}")


# ============================================================================
# EXAMPLE 5: Statistics
# ============================================================================

def example_5_statistics():
    """Get violation statistics"""
    logger.info("\n" + "=" * 70)
    logger.info("EXAMPLE 5: Statistics")
    logger.info("=" * 70)
    
    with get_db_context() as db:
        # Get stats for last 24 hours
        stats = get_violation_stats(db, hours=24)
        
        logger.info(f"Violations (24h): {stats['total']}")
        logger.info(f"  By type: {stats['by_type']}")
        logger.info(f"  Synced: {stats['synced']}")
        logger.info(f"  Unsynced: {stats['unsynced']}")
        logger.info(f"  Avg confidence: {stats['avg_confidence']:.2f}")
        logger.info(f"  With plates: {stats['with_plates']}")


# ============================================================================
# EXAMPLE 6: Integration with Main Pipeline
# ============================================================================

def example_6_pipeline_integration():
    """Show how to integrate database with main pipeline"""
    logger.info("\n" + "=" * 70)
    logger.info("EXAMPLE 6: Pipeline Integration")
    logger.info("=" * 70)
    
    logger.info("""
    # In main_pipeline.py, Thread 4 (LogThread), after line 563:
    
    # After running OCR/SRGAN/GPS, create violation data
    violation_data = {
        'violation_type': violation.get('violation_type'),
        'confidence': violation.get('confidence'),
        'plate_number': plate_result.get('text'),
        'plate_confidence': plate_result.get('confidence'),
        'latitude': gps_coords[0],
        'longitude': gps_coords[1],
        'image_path': frame_path,
        'sha256_hash': compute_sha256(frame_path),
        'srgan_used': srgan_applied,
        'platform': get_platform_name(),
    }
    
    # Save to database
    with get_db_context() as db:
        saved = save_violation(db, violation_data)
        if saved:
            log_entry.violation_id = saved.id
        else:
            logger.error("Failed to save violation to database")
    """)


# ============================================================================
# EXAMPLE 7: Querying Near Location
# ============================================================================

def example_7_location_query():
    """Query violations near a GPS location"""
    logger.info("\n" + "=" * 70)
    logger.info("EXAMPLE 7: Location-Based Query")
    logger.info("=" * 70)
    
    from backend.database.crud import get_violations_near_location
    
    with get_db_context() as db:
        # Find all violations within 500m of a location
        nearby = get_violations_near_location(
            db,
            latitude=18.5204,
            longitude=73.8567,
            radius_km=0.5
        )
        
        logger.info(f"Found {len(nearby)} violations within 500m")
        for v in nearby:
            logger.info(f"  {v.violation_type}: {v.plate_number}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all examples"""
    try:
        # Setup
        example_1_setup()
        
        # Save violations
        example_2_save_violations()
        
        # Query violations
        example_3_query_violations()
        
        # Cloud sync
        example_4_cloud_sync()
        
        # Statistics
        example_5_statistics()
        
        # Pipeline integration
        example_6_pipeline_integration()
        
        # Location query
        example_7_location_query()
        
        logger.info("\n" + "=" * 70)
        logger.info("All examples completed successfully!")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"Example error: {e}", exc_info=True)
    finally:
        # Cleanup
        shutdown()


if __name__ == "__main__":
    main()
