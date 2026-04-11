"""
SQLAlchemy Models for Traffic Violation Detection Database

Models:
    - Violation: Individual detected violations
    - FraudCheck: Fraud investigation claims
    - SyncLog: Cloud synchronization tracking (future)

Supports:
    - Local Storage: SQLite (default)
    - Cloud Storage: PostgreSQL
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

Base = declarative_base()


class Violation(Base):
    """
    Traffic Violation Record
    
    Stores detected traffic violations with evidence, confidence scores,
    and cloud synchronization status.
    
    Attributes:
        id: Unique identifier (auto-increment)
        timestamp: When violation occurred (UTC)
        violation_type: Type of violation (without_helmet, triple_ride, etc.)
        plate_number: Detected license plate (from OCR)
        plate_confidence: OCR confidence score (0-1)
        confidence: YOLO detection confidence (0-1)
        latitude: GPS latitude of violation
        longitude: GPS longitude of violation
        image_path: Path to evidence image file
        sha256_hash: SHA256 hash of image (for deduplication)
        llm_verified: Whether LLM has verified the violation
        llm_confidence: LLM verification confidence (0-1)
        srgan_used: Whether plate was upscaled with SRGAN
        platform: Hardware platform (raspberry_pi, laptop_cpu, desktop_gpu)
        synced_to_cloud: Whether synced to cloud database
    """
    
    __tablename__ = "violations"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Timestamp
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    
    # Violation Details
    violation_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="without_helmet, triple_ride, traffic_violation, etc."
    )
    
    # License Plate (from OCR)
    plate_number = Column(
        String(20),
        nullable=True,
        index=True,
        comment="Detected license plate number"
    )
    plate_confidence = Column(
        Float,
        nullable=True,
        comment="OCR confidence for plate recognition (0-1)"
    )
    
    # Detection Confidence
    confidence = Column(
        Float,
        nullable=False,
        comment="YOLO detection confidence (0-1)"
    )
    
    # GPS Location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Evidence Image
    image_path = Column(
        String(500),
        nullable=False,
        comment="Path to saved evidence image"
    )
    sha256_hash = Column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        comment="SHA256 hash of image (for deduplication)"
    )
    
    # LLM Verification
    llm_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Has LLM verified this violation?"
    )
    llm_confidence = Column(
        Float,
        nullable=True,
        comment="LLM confidence score if verified (0-1)"
    )
    
    # Enhancement Used
    srgan_used = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Was SRGAN upscaling applied to plate?"
    )
    
    # Platform Info
    platform = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Detection platform (raspberry_pi, laptop_cpu, desktop_gpu)"
    )
    
    # Cloud Sync Status
    synced_to_cloud = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Has this been synced to cloud?"
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index('ix_violation_timestamp', 'timestamp'),
        Index('ix_violation_type', 'violation_type'),
        Index('ix_violation_plate', 'plate_number'),
        Index('ix_violation_synced', 'synced_to_cloud'),
        Index('ix_violation_location', 'latitude', 'longitude'),
        Index('ix_violation_platform', 'platform'),
    )
    
    def __repr__(self):
        return (
            f"<Violation(id={self.id}, type={self.violation_type}, "
            f"plate={self.plate_number}, confidence={self.confidence:.2f})>"
        )
    
    def to_dict(self):
        """Convert violation to dictionary"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'violation_type': self.violation_type,
            'plate_number': self.plate_number,
            'plate_confidence': self.plate_confidence,
            'confidence': self.confidence,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'image_path': self.image_path,
            'llm_verified': self.llm_verified,
            'llm_confidence': self.llm_confidence,
            'srgan_used': self.srgan_used,
            'platform': self.platform,
            'synced_to_cloud': self.synced_to_cloud,
        }


class FraudCheck(Base):
    """
    Fraud Investigation Record
    
    Stores fraud investigation claims with footage search results
    and AI fault analysis.
    
    Attributes:
        id: Unique identifier
        claim_timestamp: When the claim was made
        claim_location_lat: Latitude of claimed violation
        claim_location_lng: Longitude of claimed violation
        search_radius_meters: Search radius for footage
        footage_found: Whether matching footage was found
        ai_fault_analysis: LLM analysis result (JSON string)
        fraud_score: Likelihood of fraud (0-1, higher = more suspicious)
        created_at: When record was created
    """
    
    __tablename__ = "fraud_checks"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Claim Details
    claim_timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="When the claim was made"
    )
    
    # Location (where violation was claimed)
    claim_location_lat = Column(Float, nullable=False)
    claim_location_lng = Column(Float, nullable=False)
    
    # Search Parameters
    search_radius_meters = Column(
        Integer,
        default=200,
        nullable=False,
        comment="Radius around claim location to search for footage"
    )
    
    # Investigation Results
    footage_found = Column(
        Boolean,
        nullable=False,
        index=True,
        comment="Was matching footage found?"
    )
    
    # LLM Analysis
    ai_fault_analysis = Column(
        Text,
        nullable=True,
        comment="JSON string with LLM fault analysis"
    )
    
    # Fraud Score
    fraud_score = Column(
        Float,
        nullable=False,
        comment="Fraud likelihood (0-1, higher = more suspicious)"
    )
    
    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index('ix_fraud_claim_timestamp', 'claim_timestamp'),
        Index('ix_fraud_created_at', 'created_at'),
        Index('ix_fraud_location', 'claim_location_lat', 'claim_location_lng'),
        Index('ix_fraud_found', 'footage_found'),
    )
    
    def __repr__(self):
        return (
            f"<FraudCheck(id={self.id}, footage_found={self.footage_found}, "
            f"fraud_score={self.fraud_score:.2f})>"
        )
    
    def to_dict(self):
        """Convert fraud check to dictionary"""
        return {
            'id': self.id,
            'claim_timestamp': self.claim_timestamp.isoformat() if self.claim_timestamp else None,
            'claim_location_lat': self.claim_location_lat,
            'claim_location_lng': self.claim_location_lng,
            'search_radius_meters': self.search_radius_meters,
            'footage_found': self.footage_found,
            'ai_fault_analysis': self.ai_fault_analysis,
            'fraud_score': self.fraud_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class SyncLog(Base):
    """
    Cloud Synchronization Log (for future use)
    
    Tracks synchronization attempts to cloud database.
    """
    
    __tablename__ = "sync_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    violation_id = Column(
        Integer,
        nullable=False,
        index=True,
        comment="Foreign key to violation"
    )
    
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    status = Column(
        String(50),
        nullable=False,
        comment="success, failed, pending"
    )
    
    error_message = Column(
        Text,
        nullable=True,
        comment="Error details if sync failed"
    )
    
    __table_args__ = (
        Index('ix_sync_violation', 'violation_id'),
        Index('ix_sync_timestamp', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<SyncLog(violation_id={self.violation_id}, status={self.status})>"
