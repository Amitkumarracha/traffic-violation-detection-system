"""
CRUD Operations for Traffic Violation Database

Functions for Create, Read, Update operations on:
    - Violations
    - Fraud Checks
    - Sync Logs

Usage:
    from backend.database.crud import save_violation, get_violations
    from backend.database.connection import get_db_context
    
    with get_db_context() as db:
        violation = save_violation(db, violation_data)
        all_violations = get_violations(db)
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.database.models import Violation, FraudCheck, SyncLog

logger = logging.getLogger(__name__)


# ============================================================================
# VIOLATION OPERATIONS
# ============================================================================

def save_violation(db: Session, violation_data: Dict[str, Any]) -> Optional[Violation]:
    """
    Save a detected violation to database.
    
    Args:
        db: SQLAlchemy Session
        violation_data: Dictionary with violation details
            Required: violation_type, confidence, image_path, sha256_hash, platform
            Optional: plate_number, plate_confidence, latitude, longitude, 
                     llm_verified, llm_confidence, srgan_used
    
    Returns:
        Violation object if saved, None if failed
    
    Example:
        violation = save_violation(db, {
            'violation_type': 'without_helmet',
            'confidence': 0.95,
            'plate_number': 'MH12AB1234',
            'plate_confidence': 0.87,
            'latitude': 18.5204,
            'longitude': 73.8567,
            'image_path': '/path/to/image.jpg',
            'sha256_hash': 'abc123...',
            'srgan_used': False,
            'platform': 'laptop_cpu'
        })
    """
    try:
        # Check if violation with same hash already exists (deduplication)
        existing = db.query(Violation).filter(
            Violation.sha256_hash == violation_data.get('sha256_hash')
        ).first()
        
        if existing:
            logger.warning(
                f"Duplicate violation detected (hash: {violation_data.get('sha256_hash')}). "
                f"Skipping."
            )
            return existing
        
        # Create violation object
        violation = Violation(
            violation_type=violation_data.get('violation_type'),
            plate_number=violation_data.get('plate_number'),
            plate_confidence=violation_data.get('plate_confidence'),
            confidence=violation_data.get('confidence'),
            latitude=violation_data.get('latitude'),
            longitude=violation_data.get('longitude'),
            image_path=violation_data.get('image_path'),
            sha256_hash=violation_data.get('sha256_hash'),
            llm_verified=violation_data.get('llm_verified', False),
            llm_confidence=violation_data.get('llm_confidence'),
            srgan_used=violation_data.get('srgan_used', False),
            platform=violation_data.get('platform'),
            synced_to_cloud=False,
        )
        
        # Add to session and commit
        db.add(violation)
        db.commit()
        db.refresh(violation)
        
        logger.info(
            f"Violation saved: {violation.violation_type} | "
            f"Plate: {violation.plate_number} | ID: {violation.id}"
        )
        
        return violation
    
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error saving violation: {e}")
        return None
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error saving violation: {e}")
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error saving violation: {e}")
        return None


def get_violations(db: Session, skip: int = 0, limit: int = 100) -> List[Violation]:
    """
    Get all violations with pagination.
    
    Args:
        db: SQLAlchemy Session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
    
    Returns:
        List of Violation objects
    
    Example:
        violations = get_violations(db, skip=0, limit=50)
        for v in violations:
            print(f"{v.violation_type}: {v.plate_number}")
    """
    try:
        violations = db.query(Violation).order_by(
            desc(Violation.timestamp)
        ).offset(skip).limit(limit).all()
        
        logger.info(f"Retrieved {len(violations)} violations")
        return violations
    
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving violations: {e}")
        return []


def get_violations_by_type(db: Session, violation_type: str, limit: int = 100) -> List[Violation]:
    """
    Get violations filtered by type.
    
    Args:
        db: SQLAlchemy Session
        violation_type: Type of violation (without_helmet, triple_ride, etc.)
        limit: Maximum number to return
    
    Returns:
        List of Violation objects
    
    Example:
        helmets = get_violations_by_type(db, 'without_helmet', limit=50)
    """
    try:
        violations = db.query(Violation).filter(
            Violation.violation_type == violation_type
        ).order_by(desc(Violation.timestamp)).limit(limit).all()
        
        logger.info(f"Retrieved {len(violations)} {violation_type} violations")
        return violations
    
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving violations by type: {e}")
        return []


def get_violations_by_plate(db: Session, plate_number: str) -> List[Violation]:
    """
    Get all violations for a specific license plate.
    
    Args:
        db: SQLAlchemy Session
        plate_number: License plate number
    
    Returns:
        List of Violation objects
    
    Example:
        plate_violations = get_violations_by_plate(db, 'MH12AB1234')
    """
    try:
        violations = db.query(Violation).filter(
            Violation.plate_number == plate_number
        ).order_by(desc(Violation.timestamp)).all()
        
        logger.info(f"Retrieved {len(violations)} violations for plate {plate_number}")
        return violations
    
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving violations by plate: {e}")
        return []


def get_violations_near_location(
    db: Session,
    latitude: float,
    longitude: float,
    radius_km: float = 0.2
) -> List[Violation]:
    """
    Get violations near a specific GPS location.
    
    Uses simple Euclidean distance (good for short distances).
    For exact distances, use PostGIS with PostgreSQL.
    
    Args:
        db: SQLAlchemy Session
        latitude: Center latitude
        longitude: Center longitude
        radius_km: Search radius in kilometers (default 200m)
    
    Returns:
        List of Violation objects
    
    Example:
        nearby = get_violations_near_location(db, 18.5204, 73.8567, radius_km=0.5)
    """
    try:
        # Approximate: 1 degree ≈ 111 km
        lat_offset = radius_km / 111.0
        lon_offset = radius_km / (111.0 * abs((latitude**2 - 1)**0.5))
        
        violations = db.query(Violation).filter(
            and_(
                Violation.latitude.isnot(None),
                Violation.longitude.isnot(None),
                Violation.latitude.between(latitude - lat_offset, latitude + lat_offset),
                Violation.longitude.between(longitude - lon_offset, longitude + lon_offset)
            )
        ).order_by(desc(Violation.timestamp)).all()
        
        logger.info(
            f"Retrieved {len(violations)} violations near "
            f"({latitude:.4f}, {longitude:.4f}) within {radius_km}km"
        )
        return violations
    
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving violations by location: {e}")
        return []


def get_unsynced_violations(db: Session, limit: int = 100) -> List[Violation]:
    """
    Get violations not yet synced to cloud.
    
    Used for batch cloud synchronization.
    
    Args:
        db: SQLAlchemy Session
        limit: Maximum number to return
    
    Returns:
        List of Violation objects
    
    Example:
        to_sync = get_unsynced_violations(db, limit=50)
        for v in to_sync:
            sync_to_cloud(v)
    """
    try:
        violations = db.query(Violation).filter(
            Violation.synced_to_cloud == False
        ).order_by(Violation.timestamp).limit(limit).all()
        
        logger.info(f"Retrieved {len(violations)} unsynced violations")
        return violations
    
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving unsynced violations: {e}")
        return []


def mark_synced(db: Session, violation_id: int) -> bool:
    """
    Mark a violation as synced to cloud.
    
    Args:
        db: SQLAlchemy Session
        violation_id: ID of violation to mark
    
    Returns:
        True if successful, False otherwise
    
    Example:
        if mark_synced(db, violation_id):
            print("Marked as synced")
    """
    try:
        violation = db.query(Violation).filter(
            Violation.id == violation_id
        ).first()
        
        if not violation:
            logger.warning(f"Violation {violation_id} not found")
            return False
        
        violation.synced_to_cloud = True
        db.commit()
        
        logger.info(f"Marked violation {violation_id} as synced")
        return True
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error marking violation as synced: {e}")
        return False


def get_violation_stats(db: Session, hours: int = 24) -> Dict[str, Any]:
    """
    Get violation statistics for recent period.
    
    Args:
        db: SQLAlchemy Session
        hours: Look back period in hours
    
    Returns:
        Dictionary with statistics
    
    Example:
        stats = get_violation_stats(db, hours=1)
        print(f"Violations in last hour: {stats['total']}")
        print(f"By type: {stats['by_type']}")
    """
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Total violations
        total = db.query(Violation).filter(
            Violation.timestamp >= cutoff_time
        ).count()
        
        # By type
        by_type = {}
        type_results = db.query(
            Violation.violation_type,
            func.count(Violation.id)
        ).filter(
            Violation.timestamp >= cutoff_time
        ).group_by(Violation.violation_type).all()
        
        for v_type, count in type_results:
            by_type[v_type] = count
        
        # Synced vs unsynced
        synced = db.query(Violation).filter(
            and_(
                Violation.timestamp >= cutoff_time,
                Violation.synced_to_cloud == True
            )
        ).count()
        
        # Average confidence
        avg_confidence = db.query(
            func.avg(Violation.confidence)
        ).filter(
            Violation.timestamp >= cutoff_time
        ).scalar() or 0.0
        
        # With plates
        with_plates = db.query(Violation).filter(
            and_(
                Violation.timestamp >= cutoff_time,
                Violation.plate_number.isnot(None)
            )
        ).count()
        
        stats = {
            'total': total,
            'by_type': by_type,
            'synced': synced,
            'unsynced': total - synced,
            'avg_confidence': round(float(avg_confidence), 3),
            'with_plates': with_plates,
            'period_hours': hours,
        }
        
        logger.info(f"Statistics: {total} violations in last {hours}h")
        return stats
    
    except SQLAlchemyError as e:
        logger.error(f"Database error getting statistics: {e}")
        return {}


# ============================================================================
# FRAUD CHECK OPERATIONS
# ============================================================================

def save_fraud_check(db: Session, fraud_data: Dict[str, Any]) -> Optional[FraudCheck]:
    """
    Save a fraud investigation check.
    
    Args:
        db: SQLAlchemy Session
        fraud_data: Dictionary with fraud check details
            Required: claim_location_lat, claim_location_lng, footage_found, fraud_score
            Optional: search_radius_meters, ai_fault_analysis
    
    Returns:
        FraudCheck object if saved, None if failed
    
    Example:
        fraud = save_fraud_check(db, {
            'claim_timestamp': datetime.now(timezone.utc),
            'claim_location_lat': 18.5204,
            'claim_location_lng': 73.8567,
            'footage_found': True,
            'fraud_score': 0.15,
            'ai_fault_analysis': '{"analysis": "..."}'
        })
    """
    try:
        fraud_check = FraudCheck(
            claim_timestamp=fraud_data.get('claim_timestamp', datetime.now(timezone.utc)),
            claim_location_lat=fraud_data.get('claim_location_lat'),
            claim_location_lng=fraud_data.get('claim_location_lng'),
            search_radius_meters=fraud_data.get('search_radius_meters', 200),
            footage_found=fraud_data.get('footage_found'),
            ai_fault_analysis=fraud_data.get('ai_fault_analysis'),
            fraud_score=fraud_data.get('fraud_score'),
        )
        
        db.add(fraud_check)
        db.commit()
        db.refresh(fraud_check)
        
        logger.info(
            f"Fraud check saved: footage_found={fraud_check.footage_found}, "
            f"fraud_score={fraud_check.fraud_score:.2f}, ID={fraud_check.id}"
        )
        
        return fraud_check
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error saving fraud check: {e}")
        return None
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error saving fraud check: {e}")
        return None


def get_fraud_checks(db: Session, skip: int = 0, limit: int = 100) -> List[FraudCheck]:
    """
    Get all fraud checks with pagination.
    
    Args:
        db: SQLAlchemy Session
        skip: Number of records to skip
        limit: Maximum number to return
    
    Returns:
        List of FraudCheck objects
    """
    try:
        checks = db.query(FraudCheck).order_by(
            desc(FraudCheck.created_at)
        ).offset(skip).limit(limit).all()
        
        logger.info(f"Retrieved {len(checks)} fraud checks")
        return checks
    
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving fraud checks: {e}")
        return []


def get_high_fraud_checks(db: Session, threshold: float = 0.7) -> List[FraudCheck]:
    """
    Get fraud checks with high fraud scores.
    
    Args:
        db: SQLAlchemy Session
        threshold: Fraud score threshold (0-1)
    
    Returns:
        List of FraudCheck objects
    """
    try:
        checks = db.query(FraudCheck).filter(
            FraudCheck.fraud_score >= threshold
        ).order_by(desc(FraudCheck.fraud_score)).all()
        
        logger.info(f"Retrieved {len(checks)} high-fraud checks (threshold={threshold})")
        return checks
    
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving high-fraud checks: {e}")
        return []


# ============================================================================
# SYNC LOG OPERATIONS
# ============================================================================

def log_sync_attempt(
    db: Session,
    violation_id: int,
    status: str,
    error_message: Optional[str] = None
) -> Optional[SyncLog]:
    """
    Log a synchronization attempt.
    
    Args:
        db: SQLAlchemy Session
        violation_id: ID of violation being synced
        status: sync status (success, failed, pending)
        error_message: Error details if sync failed
    
    Returns:
        SyncLog object if saved, None if failed
    """
    try:
        log = SyncLog(
            violation_id=violation_id,
            status=status,
            error_message=error_message,
        )
        
        db.add(log)
        db.commit()
        db.refresh(log)
        
        logger.debug(f"Logged sync attempt: violation_id={violation_id}, status={status}")
        return log
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error logging sync attempt: {e}")
        return None


def get_sync_logs(db: Session, violation_id: int) -> List[SyncLog]:
    """
    Get sync logs for a violation.
    
    Args:
        db: SQLAlchemy Session
        violation_id: ID of violation
    
    Returns:
        List of SyncLog objects
    """
    try:
        logs = db.query(SyncLog).filter(
            SyncLog.violation_id == violation_id
        ).order_by(desc(SyncLog.timestamp)).all()
        
        return logs
    
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving sync logs: {e}")
        return []


# ============================================================================
# BULK OPERATIONS
# ============================================================================

def delete_old_violations(db: Session, days: int = 90) -> int:
    """
    Delete violations older than specified days.
    
    Use for data retention policies.
    
    Args:
        db: SQLAlchemy Session
        days: Delete violations older than this many days
    
    Returns:
        Number of violations deleted
    
    Example:
        deleted = delete_old_violations(db, days=365)
        print(f"Deleted {deleted} old violations")
    """
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        count = db.query(Violation).filter(
            Violation.timestamp < cutoff_date
        ).delete()
        
        db.commit()
        logger.info(f"Deleted {count} violations older than {days} days")
        return count
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error deleting old violations: {e}")
        return 0


def get_total_count(db: Session) -> int:
    """Get total number of violations in database."""
    try:
        return db.query(Violation).count()
    except SQLAlchemyError as e:
        logger.error(f"Database error getting count: {e}")
        return 0


def get_plate_statistics(db: Session) -> Dict[str, Any]:
    """Get statistics about plate detection."""
    try:
        total = db.query(Violation).count()
        with_plates = db.query(Violation).filter(
            Violation.plate_number.isnot(None)
        ).count()
        
        return {
            'total_violations': total,
            'with_plates': with_plates,
            'without_plates': total - with_plates,
            'plate_detection_rate': (with_plates / total * 100) if total > 0 else 0,
        }
    except SQLAlchemyError as e:
        logger.error(f"Database error getting plate stats: {e}")
        return {}
