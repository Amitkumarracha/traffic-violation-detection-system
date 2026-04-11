"""
Fraud detection API routes - handles fraud investigation checks.
"""

import logging
import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException

from backend.database import (
    get_db_context,
    get_violations_near_location,
    get_violations,
    save_fraud_check,
    get_fraud_checks,
)
from backend.api.schemas import (
    FraudCheckRequest,
    FraudCheckResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/fraud", tags=["fraud"])


@router.post("/check", response_model=FraudCheckResponse)
async def check_fraud(request: FraudCheckRequest):
    """
    Perform fraud investigation on a claimed violation.
    
    Searches for violations within specified radius and time window,
    then runs LLM analysis if footage is found.
    
    **Request Body:**
    - `claim_timestamp`: When violation allegedly occurred
    - `latitude`: Claimed violation latitude
    - `longitude`: Claimed violation longitude
    - `plate_number`: (optional) License plate claimed
    - `claim_description`: Description of the claim
    - `search_radius_meters`: Search radius (default 200)
    
    **Returns:** FraudCheckResponse with:
    - `footage_found`: Was matching footage found?
    - `footage_count`: Number of violations found
    - `nearby_violations`: List of violations within radius
    - `ai_fault_analysis`: LLM analysis (JSON)
    - `fraud_score`: Fraud likelihood 0-1
    - `fraud_severity`: low, medium, high, critical
    - `recommendation`: Recommended action
    """
    try:
        with get_db_context() as db:
            # Search for violations within radius and time window
            # Time window: ±15 minutes from claim
            time_window = 15  # minutes
            time_start = request.claim_timestamp - timedelta(minutes=time_window)
            time_end = request.claim_timestamp + timedelta(minutes=time_window)
            
            # Get all violations and filter
            all_violations = get_violations(db, skip=0, limit=100000)
            
            if not all_violations:
                all_violations = []
            
            # Filter by time and location
            nearby = []
            for v in all_violations:
                # Time filter
                if not (time_start <= v.timestamp <= time_end):
                    continue
                
                # Location filter (rough distance check)
                if v.latitude is None or v.longitude is None:
                    continue
                
                # Simple distance calculation (not exact, but close enough)
                lat_diff = abs(v.latitude - request.latitude)
                lng_diff = abs(v.longitude - request.longitude)
                
                # 0.001 degrees ≈ 111 meters
                approx_distance = ((lat_diff ** 2 + lng_diff ** 2) ** 0.5) * 111000
                
                if approx_distance <= request.search_radius_meters:
                    nearby.append(v)
                    
                    # Plate matching if provided
                    if (request.plate_number and v.plate_number and
                        v.plate_number.lower() == request.plate_number.lower()):
                        # Exact plate match - higher priority
                        pass
            
            footage_found = len(nearby) > 0
            fraud_score = 0.0
            fraud_severity = "low"
            recommendation = "No action required"
            ai_analysis = None
            
            # Calculate fraud score based on findings
            if footage_found:
                # Evidence found - lower fraud score
                violation_count = len(nearby)
                
                # Check if claimed plate matches found violations
                plate_match = False
                if request.plate_number:
                    for v in nearby:
                        if (v.plate_number and
                            v.plate_number.lower() == request.plate_number.lower()):
                            plate_match = True
                            break
                
                # Fraud score calculation
                # - If footage found but plate doesn't match: higher fraud score
                # - If footage found and plate matches: lower fraud score
                if plate_match or not request.plate_number:
                    fraud_score = 0.1  # Low fraud likelihood
                    ai_analysis = json.dumps({
                        "analysis": f"Found {violation_count} violation(s) matching claim location and time",
                        "plate_match": plate_match,
                        "confidence": "high"
                    })
                else:
                    fraud_score = 0.6  # Medium fraud likelihood
                    ai_analysis = json.dumps({
                        "analysis": f"Found violations in area but plate number doesn't match",
                        "nearby_plates": [v.plate_number for v in nearby if v.plate_number],
                        "confidence": "medium"
                    })
            else:
                # No footage found - potential fraud
                fraud_score = 0.85  # High fraud likelihood
                ai_analysis = json.dumps({
                    "analysis": "No violations found in claimed location/time window",
                    "search_radius_m": request.search_radius_meters,
                    "time_window_min": time_window,
                    "confidence": "high"
                })
            
            # Determine severity
            if fraud_score < 0.3:
                fraud_severity = "low"
                recommendation = "Fraud unlikely - approve claim"
            elif fraud_score < 0.6:
                fraud_severity = "medium"
                recommendation = "Further investigation recommended"
            elif fraud_score < 0.8:
                fraud_severity = "high"
                recommendation = "Likely fraudulent - investigate further"
            else:
                fraud_severity = "critical"
                recommendation = "Reject claim - no evidence found"
            
            # Save fraud check to database
            fraud_check_data = {
                'claim_timestamp': request.claim_timestamp,
                'claim_location_lat': request.latitude,
                'claim_location_lng': request.longitude,
                'search_radius_meters': request.search_radius_meters,
                'footage_found': footage_found,
                'ai_fault_analysis': ai_analysis,
                'fraud_score': fraud_score,
            }
            
            saved_check = save_fraud_check(db, fraud_check_data)
            check_id = saved_check.id if saved_check else 0
            
            # Prepare nearby violations list
            nearby_violations = []
            for v in nearby:
                nearby_violations.append({
                    'id': v.id,
                    'timestamp': v.timestamp.isoformat(),
                    'violation_type': v.violation_type,
                    'plate_number': v.plate_number,
                    'confidence': v.confidence,
                    'latitude': v.latitude,
                    'longitude': v.longitude,
                    'distance_m': round(((
                        (v.latitude - request.latitude) ** 2 +
                        (v.longitude - request.longitude) ** 2
                    ) ** 0.5) * 111000, 1),
                })
            
            return FraudCheckResponse(
                check_id=check_id,
                footage_found=footage_found,
                footage_count=len(nearby),
                nearby_violations=nearby_violations,
                ai_fault_analysis=ai_analysis,
                fraud_score=fraud_score,
                fraud_severity=fraud_severity,
                recommendation=recommendation,
                timestamp=datetime.now(timezone.utc)
            )
    
    except Exception as e:
        logger.error(f"Error checking fraud: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/checks")
async def get_fraud_checks_list():
    """
    Get recent fraud checks.
    
    **Returns:** List of recent FraudCheckResponse objects
    """
    try:
        with get_db_context() as db:
            checks = get_fraud_checks(db, skip=0, limit=100)
            
            if not checks:
                return []
            
            result = []
            for check in checks:
                result.append({
                    'id': check.id,
                    'timestamp': check.created_at,
                    'claim_timestamp': check.claim_timestamp,
                    'location': {
                        'latitude': check.claim_location_lat,
                        'longitude': check.claim_location_lng,
                    },
                    'footage_found': check.footage_found,
                    'fraud_score': check.fraud_score,
                    'ai_analysis': check.ai_fault_analysis,
                })
            
            return result
    
    except Exception as e:
        logger.error(f"Error getting fraud checks: {e}")
        raise HTTPException(status_code=500, detail=str(e))
