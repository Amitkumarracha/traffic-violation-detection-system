"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field


# =====================
# VIOLATION SCHEMAS
# =====================

class ViolationResponse(BaseModel):
    """Response schema for violation details."""
    
    id: int = Field(..., description="Unique violation ID")
    timestamp: datetime = Field(..., description="When violation occurred (UTC)")
    violation_type: str = Field(..., description="Type: without_helmet, triple_ride, etc.")
    plate_number: Optional[str] = Field(None, description="Detected license plate")
    plate_confidence: Optional[float] = Field(None, description="OCR confidence 0-1")
    confidence: float = Field(..., description="YOLO detection confidence 0-1")
    latitude: Optional[float] = Field(None, description="GPS latitude")
    longitude: Optional[float] = Field(None, description="GPS longitude")
    image_url: Optional[str] = Field(None, description="URL to evidence image")
    sha256_hash: str = Field(..., description="Image hash for deduplication")
    llm_verified: bool = Field(default=False, description="LLM verification status")
    llm_confidence: Optional[float] = Field(None, description="LLM confidence 0-1")
    srgan_used: bool = Field(default=False, description="Whether plate was upscaled")
    platform: str = Field(..., description="Detection platform (laptop_cpu, rpi, etc.)")
    synced_to_cloud: bool = Field(default=False, description="Cloud sync status")
    created_at: datetime = Field(..., description="When record created in DB")
    
    class Config:
        from_attributes = True


class ViolationListResponse(BaseModel):
    """Response schema for paginated violations list."""
    
    total: int = Field(..., description="Total violations in database")
    skip: int = Field(..., description="Pagination skip offset")
    limit: int = Field(..., description="Pagination limit")
    violations: List[ViolationResponse] = Field(..., description="List of violations")


class ViolationStatsResponse(BaseModel):
    """Response schema for violation statistics."""
    
    total_count: int = Field(..., description="Total violations all time")
    today_count: int = Field(..., description="Violations detected today")
    by_type: Dict[str, int] = Field(..., description="Count by violation type")
    avg_confidence: float = Field(..., description="Average detection confidence")
    avg_plate_confidence: float = Field(..., description="Average OCR confidence")
    with_plates: int = Field(..., description="Violations with detected plates")
    without_plates: int = Field(..., description="Violations without plates")
    plate_detection_rate: float = Field(..., description="Plate detection percentage 0-100")
    hourly_distribution: Dict[int, int] = Field(..., description="Hour (0-23) -> count")
    top_locations: List[Dict[str, Any]] = Field(
        ..., 
        description="Top GPS clusters with {lat, lng, count}"
    )
    by_platform: Dict[str, int] = Field(..., description="Count by platform")
    synced_count: int = Field(..., description="Violations synced to cloud")
    unsynced_count: int = Field(..., description="Violations not synced")


class VerifyViolationRequest(BaseModel):
    """Request schema for manually triggering LLM verification."""
    
    use_gemini: bool = Field(default=True, description="Use Gemini for verification")
    reprocess: bool = Field(default=False, description="Force reprocess even if verified")


class VerifyViolationResponse(BaseModel):
    """Response schema after verification."""
    
    violation_id: int
    llm_verified: bool
    llm_confidence: float
    verification_message: str
    timestamp: datetime


# =====================
# FRAUD CHECK SCHEMAS
# =====================

class FraudCheckRequest(BaseModel):
    """Request schema for fraud investigation."""
    
    claim_timestamp: datetime = Field(..., description="When violation allegedly occurred")
    latitude: float = Field(..., description="Claimed violation latitude")
    longitude: float = Field(..., description="Claimed violation longitude")
    plate_number: Optional[str] = Field(None, description="Plate number claimed")
    claim_description: str = Field(..., description="Description of the claim")
    search_radius_meters: int = Field(default=200, description="Search radius in meters")


class FraudCheckResponse(BaseModel):
    """Response schema for fraud investigation results."""
    
    check_id: int = Field(..., description="Fraud check ID")
    footage_found: bool = Field(..., description="Was matching video footage found?")
    footage_count: int = Field(..., description="Number of violations found nearby")
    nearby_violations: List[Dict[str, Any]] = Field(
        ..., 
        description="List of violations within search radius"
    )
    ai_fault_analysis: Optional[str] = Field(
        None, 
        description="LLM analysis of claims (JSON)"
    )
    fraud_score: float = Field(..., description="Fraud likelihood 0-1")
    fraud_severity: str = Field(
        ..., 
        description="low, medium, high, critical"
    )
    recommendation: str = Field(..., description="Recommended action")
    timestamp: datetime = Field(..., description="When check performed")


# =====================
# HEALTH CHECK SCHEMAS
# =====================

class HealthResponse(BaseModel):
    """Response schema for health check endpoint."""
    
    status: str = Field(..., description="ok, degraded, error")
    platform: str = Field(..., description="Detection platform")
    model_loaded: bool = Field(..., description="Is YOLO model loaded?")
    gpu_available: bool = Field(..., description="Is GPU available?")
    uptime_seconds: float = Field(..., description="API uptime in seconds")
    db_connection: bool = Field(..., description="Can connect to database?")
    violations_today: int = Field(..., description="Violations detected today")
    pipeline_running: bool = Field(..., description="Is pipeline thread running?")
    pipeline_fps: float = Field(..., description="Detection FPS")
    last_detection: Optional[datetime] = Field(
        None, 
        description="Timestamp of last detection"
    )
    memory_usage_mb: float = Field(..., description="Memory usage in MB")
    errors: List[str] = Field(default_factory=list, description="Error messages if any")


# =====================
# WEBSOCKET SCHEMAS
# =====================

class LiveViolationEvent(BaseModel):
    """WebSocket event for live violations."""
    
    event_type: str = Field(..., description="violation_detected, stats_update")
    timestamp: datetime
    violation_id: Optional[int] = None
    violation_type: Optional[str] = None
    confidence: Optional[float] = None
    plate_number: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    image_url: Optional[str] = None
    platform: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None


# =====================
# ERROR SCHEMAS
# =====================

class ErrorResponse(BaseModel):
    """Response schema for errors."""
    
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =====================
# PAGINATION
# =====================

class PaginationParams(BaseModel):
    """Common pagination parameters."""
    
    skip: int = Field(default=0, ge=0, description="Skip N records")
    limit: int = Field(default=50, ge=1, le=1000, description="Return N records max")
