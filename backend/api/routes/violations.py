"""
Violations API routes - handles CRUD and statistics for traffic violations.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, Query, HTTPException, File, UploadFile
from fastapi.responses import FileResponse

from backend.database import (
    get_db_context,
    get_violations,
    get_violations_by_type,
    get_violations_by_plate,
    get_violations_near_location,
    get_violation_stats,
    get_total_count,
    get_plate_statistics,
    save_violation,
)
from backend.api.schemas import (
    ViolationResponse,
    ViolationListResponse,
    ViolationStatsResponse,
    VerifyViolationRequest,
    VerifyViolationResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/violations", tags=["violations"])


# =====================
# GET VIOLATIONS
# =====================

@router.get("", response_model=ViolationListResponse)
async def list_violations(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=1000, description="Results per page"),
    violation_type: Optional[str] = Query(None, description="Filter by type"),
    plate_number: Optional[str] = Query(None, description="Filter by plate"),
    date_from: Optional[datetime] = Query(None, description="Start date (UTC)"),
    date_to: Optional[datetime] = Query(None, description="End date (UTC)"),
):
    """
    Get paginated list of violations with optional filters.
    
    **Query Parameters:**
    - `skip`: Pagination offset (default 0)
    - `limit`: Results per page (default 50, max 1000)
    - `violation_type`: Filter by type (without_helmet, triple_ride, etc.)
    - `plate_number`: Filter by license plate
    - `date_from`: Start date for range
    - `date_to`: End date for range
    
    **Returns:** Paginated ViolationResponse list
    """
    try:
        with get_db_context() as db:
            # Get total count
            total = get_total_count(db)
            
            # Get violations with filters
            if violation_type:
                violations = get_violations_by_type(db, violation_type, limit=10000)
            elif plate_number:
                violations = get_violations_by_plate(db, plate_number)
            else:
                violations = get_violations(db, skip=skip, limit=limit)
            
            # Apply additional filters
            if violations:
                if date_from:
                    violations = [v for v in violations if v.timestamp >= date_from]
                if date_to:
                    violations = [v for v in violations if v.timestamp <= date_to]
            
            # Apply pagination if not already filtered
            if not violation_type and not plate_number:
                violations = violations[skip : skip + limit]
            else:
                violations = violations[skip : skip + limit]
            
            # Convert to response models
            violation_responses = []
            for v in violations:
                v_dict = v.to_dict() if hasattr(v, 'to_dict') else {
                    'id': v.id,
                    'timestamp': v.timestamp,
                    'violation_type': v.violation_type,
                    'plate_number': v.plate_number,
                    'plate_confidence': v.plate_confidence,
                    'confidence': v.confidence,
                    'latitude': v.latitude,
                    'longitude': v.longitude,
                    'image_url': f"/api/violations/{v.id}/image",
                    'sha256_hash': v.sha256_hash,
                    'llm_verified': v.llm_verified,
                    'llm_confidence': v.llm_confidence,
                    'srgan_used': v.srgan_used,
                    'platform': v.platform,
                    'synced_to_cloud': v.synced_to_cloud,
                    'created_at': v.timestamp,
                }
                violation_responses.append(ViolationResponse(**v_dict))
            
            return ViolationListResponse(
                total=total,
                skip=skip,
                limit=limit,
                violations=violation_responses,
            )
    
    except Exception as e:
        logger.error(f"Error listing violations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{violation_id}", response_model=ViolationResponse)
async def get_violation(violation_id: int):
    """
    Get details of a specific violation.
    
    **Parameters:**
    - `violation_id`: The violation ID
    
    **Returns:** ViolationResponse with full details
    """
    try:
        with get_db_context() as db:
            violations = get_violations(db, skip=0, limit=10000)
            violation = next((v for v in violations if v.id == violation_id), None)
            
            if not violation:
                raise HTTPException(status_code=404, detail="Violation not found")
            
            v_dict = v.to_dict() if hasattr(violation, 'to_dict') else {
                'id': violation.id,
                'timestamp': violation.timestamp,
                'violation_type': violation.violation_type,
                'plate_number': violation.plate_number,
                'plate_confidence': violation.plate_confidence,
                'confidence': violation.confidence,
                'latitude': violation.latitude,
                'longitude': violation.longitude,
                'image_url': f"/api/violations/{violation.id}/image",
                'sha256_hash': violation.sha256_hash,
                'llm_verified': violation.llm_verified,
                'llm_confidence': violation.llm_confidence,
                'srgan_used': violation.srgan_used,
                'platform': violation.platform,
                'synced_to_cloud': violation.synced_to_cloud,
                'created_at': violation.timestamp,
            }
            
            return ViolationResponse(**v_dict)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting violation {violation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# STATISTICS
# =====================

@router.get("/stats/overview", response_model=ViolationStatsResponse)
async def get_violation_stats_endpoint():
    """
    Get comprehensive violation statistics.
    
    **Returns:**
    - `total_count`: Total violations all time
    - `today_count`: Violations detected today
    - `by_type`: Breakdown by violation type
    - `avg_confidence`: Average detection confidence
    - `hourly_distribution`: Violations per hour (last 24h)
    - `top_locations`: GPS clusters (top 5)
    - `by_platform`: Violations by detection platform
    - `plate_detection_rate`: Percentage with detected plates
    """
    try:
        with get_db_context() as db:
            # Get stats from database
            stats_dict = get_violation_stats(db, hours=24)
            
            # Calculate today's count
            today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            violations = get_violations(db, skip=0, limit=10000)
            today_count = sum(1 for v in violations if v.timestamp >= today)
            
            # Get plate statistics
            plate_stats = get_plate_statistics(db)
            
            # Build hourly distribution
            hourly = {}
            now = datetime.now(timezone.utc)
            for i in range(24):
                hour_start = now - timedelta(hours=24-i)
                hour_end = hour_start + timedelta(hours=1)
                count = sum(1 for v in violations 
                           if hour_start <= v.timestamp < hour_end)
                hourly[i] = count
            
            # Build top locations (simple clustering)
            locations = []
            if violations:
                # Group by 0.001 degree (roughly 100m)
                location_map = {}
                for v in violations:
                    if v.latitude and v.longitude:
                        key = (round(v.latitude, 3), round(v.longitude, 3))
                        if key not in location_map:
                            location_map[key] = []
                        location_map[key].append(v)
                
                # Get top 5 clusters
                top_clusters = sorted(
                    location_map.items(),
                    key=lambda x: len(x[1]),
                    reverse=True
                )[:5]
                
                for (lat, lng), cluster in top_clusters:
                    locations.append({
                        'latitude': lat,
                        'longitude': lng,
                        'count': len(cluster)
                    })
            
            # Build platform breakdown
            by_platform = {}
            for v in violations:
                by_platform[v.platform] = by_platform.get(v.platform, 0) + 1
            
            return ViolationStatsResponse(
                total_count=stats_dict.get('total', 0),
                today_count=today_count,
                by_type=stats_dict.get('by_type', {}),
                avg_confidence=stats_dict.get('avg_confidence', 0.0),
                avg_plate_confidence=stats_dict.get('avg_plate_confidence', 0.0),
                with_plates=plate_stats.get('with_plates', 0),
                without_plates=plate_stats.get('without_plates', 0),
                plate_detection_rate=plate_stats.get('plate_detection_rate', 0.0),
                hourly_distribution=hourly,
                top_locations=locations,
                by_platform=by_platform,
                synced_count=sum(1 for v in violations if v.synced_to_cloud),
                unsynced_count=sum(1 for v in violations if not v.synced_to_cloud),
            )
    
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# IMAGE SERVING
# =====================

@router.get("/{violation_id}/image")
async def get_violation_image(violation_id: int):
    """
    Get the evidence image for a violation.
    
    **Parameters:**
    - `violation_id`: The violation ID
    
    **Returns:** Image file (JPEG/PNG)
    """
    try:
        with get_db_context() as db:
            violations = get_violations(db, skip=0, limit=10000)
            violation = next((v for v in violations if v.id == violation_id), None)
            
            if not violation:
                raise HTTPException(status_code=404, detail="Violation not found")
            
            image_path = Path(violation.image_path)
            
            if not image_path.exists():
                raise HTTPException(status_code=404, detail="Image file not found")
            
            return FileResponse(
                image_path,
                media_type="image/jpeg",
                filename=f"violation_{violation_id}.jpg"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving image for violation {violation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# VERIFICATION
# =====================

@router.post("/{violation_id}/verify", response_model=VerifyViolationResponse)
async def verify_violation(
    violation_id: int,
    request: VerifyViolationRequest
):
    """
    Trigger LLM verification for a specific violation.
    
    **Parameters:**
    - `violation_id`: The violation ID
    - `request.use_gemini`: Use Google Gemini for verification
    - `request.reprocess`: Force reprocess even if already verified
    
    **Returns:** Updated violation with llm_confidence
    """
    try:
        with get_db_context() as db:
            violations = get_violations(db, skip=0, limit=10000)
            violation = next((v for v in violations if v.id == violation_id), None)
            
            if not violation:
                raise HTTPException(status_code=404, detail="Violation not found")
            
            # Check if already verified
            if violation.llm_verified and not request.reprocess:
                return VerifyViolationResponse(
                    violation_id=violation.id,
                    llm_verified=True,
                    llm_confidence=violation.llm_confidence or 0.0,
                    verification_message="Already verified",
                    timestamp=datetime.now(timezone.utc)
                )
            
            # TODO: Integrate with Gemini LLM verification
            # For now, return mock response
            logger.info(f"Verification triggered for violation {violation_id}")
            
            return VerifyViolationResponse(
                violation_id=violation.id,
                llm_verified=True,
                llm_confidence=0.95,
                verification_message="Verification completed (mock)",
                timestamp=datetime.now(timezone.utc)
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying violation {violation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# EXPORT VIOLATIONS
# =====================

@router.get("/export")
async def export_violations(
    format: str = Query("csv", description="Export format (csv)"),
    violation_type: Optional[str] = Query(None, description="Filter by type"),
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
):
    """Export violations to CSV format"""
    import csv
    import io
    from fastapi.responses import StreamingResponse
    
    try:
        with get_db_context() as db:
            # Get violations with filters
            violations = get_violations(db, skip=0, limit=10000)
            
            # Filter by type if specified
            if violation_type:
                violations = [v for v in violations if v.violation_type == violation_type]
            
            # Filter by date range
            if date_from:
                violations = [v for v in violations if v.timestamp >= date_from]
            if date_to:
                violations = [v for v in violations if v.timestamp <= date_to]
            
            # Create CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'ID', 'Timestamp', 'Violation Type', 'Plate Number', 
                'Confidence', 'Latitude', 'Longitude', 'Platform', 
                'LLM Verified', 'SRGAN Used'
            ])
            
            # Write data
            for v in violations:
                writer.writerow([
                    v.id,
                    v.timestamp.isoformat(),
                    v.violation_type,
                    v.plate_number or '',
                    f"{v.confidence:.2f}",
                    v.latitude or '',
                    v.longitude or '',
                    v.platform or '',
                    'Yes' if v.llm_verified else 'No',
                    'Yes' if v.srgan_used else 'No'
                ])
            
            # Return as downloadable file
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=violations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                }
            )
            
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
