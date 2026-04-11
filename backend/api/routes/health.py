"""
Health check API routes - monitor system status and performance.
"""

import logging
import psutil
import time
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException

from backend.database import get_db_context, get_violations, get_total_count

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/health", tags=["health"])

# Global tracking for uptime
_start_time = time.time()
_last_detection_time = None
_pipeline_fps = 0.0


def set_last_detection():
    """Update last detection timestamp."""
    global _last_detection_time
    _last_detection_time = datetime.now(timezone.utc)


def set_pipeline_fps(fps: float):
    """Update pipeline FPS."""
    global _pipeline_fps
    _pipeline_fps = fps


@router.get("/", response_model=dict)
async def health_check():
    """
    Get system health and status.
    
    **Returns:**
    - `status`: ok, degraded, or error
    - `platform`: Detection platform (laptop_cpu, rpi, etc.)
    - `model_loaded`: Is YOLO model loaded?
    - `gpu_available`: Is GPU available?
    - `uptime_seconds`: API uptime
    - `db_connection`: Can connect to database?
    - `violations_today`: Violations detected today
    - `pipeline_running`: Is pipeline running?
    - `pipeline_fps`: Detection FPS
    - `last_detection`: Timestamp of last detection
    - `memory_usage_mb`: Memory usage
    - `errors`: List of error messages if any
    """
    errors = []
    all_ok = True
    
    try:
        # Check uptime
        uptime = time.time() - _start_time
        
        # Check database connection
        db_ok = False
        violations_today = 0
        
        try:
            with get_db_context() as db:
                db_ok = True
                
                # Get today's violations
                violations = get_violations(db, skip=0, limit=100000)
                today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                violations_today = sum(1 for v in violations if v.timestamp >= today)
        
        except Exception as e:
            db_ok = False
            errors.append(f"Database connection failed: {str(e)}")
            all_ok = False
        
        # Check memory
        try:
            process = psutil.Process()
            memory_usage_mb = process.memory_info().rss / (1024 * 1024)
        except:
            memory_usage_mb = 0.0
        
        # Check GPU (stub - would integrate with actual GPU detection)
        gpu_available = False
        try:
            # Try to detect CUDA/GPU
            import torch
            gpu_available = torch.cuda.is_available()
        except:
            pass
        
        # Check model loaded (stub)
        model_loaded = False
        try:
            # Would check if YOLO model is actually loaded
            # This is a placeholder
            model_loaded = True
        except:
            pass
        
        # Determine overall status
        status = "ok"
        if not db_ok:
            status = "error"
            all_ok = False
        elif memory_usage_mb > 3000:  # Over 3GB
            status = "degraded"
        elif not model_loaded:
            status = "degraded"
        
        return {
            "status": status,
            "platform": "laptop_cpu",  # Would come from config
            "model_loaded": model_loaded,
            "gpu_available": gpu_available,
            "uptime_seconds": uptime,
            "db_connection": db_ok,
            "violations_today": violations_today,
            "pipeline_running": True,  # Would check actual pipeline thread
            "pipeline_fps": _pipeline_fps,
            "last_detection": _last_detection_time.isoformat() if _last_detection_time else None,
            "memory_usage_mb": round(memory_usage_mb, 2),
            "errors": errors,
        }
    
    except Exception as e:
        logger.error(f"Error checking health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/live")
async def health_live():
    """
    Lightweight health check - for frequent polling.
    
    **Returns:** {status, uptime_seconds, violations_today}
    """
    try:
        uptime = time.time() - _start_time
        violations_today = 0
        
        try:
            with get_db_context() as db:
                violations = get_violations(db, skip=0, limit=100000)
                today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                violations_today = sum(1 for v in violations if v.timestamp >= today)
        except:
            pass
        
        return {
            "status": "ok",
            "uptime_seconds": uptime,
            "violations_today": violations_today,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/db")
async def db_health():
    """
    Database-specific health check.
    
    **Returns:** {connected, table_exists, violation_count, last_violation_timestamp}
    """
    try:
        with get_db_context() as db:
            total = get_total_count(db)
            violations = get_violations(db, skip=0, limit=10000)
            
            last_violation = None
            if violations:
                last_violation = max(violations, key=lambda v: v.timestamp).timestamp.isoformat()
            
            return {
                "connected": True,
                "total_violations": total,
                "last_violation_timestamp": last_violation,
                "recent_violations_count": len(violations),
            }
    
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "connected": False,
            "error": str(e),
        }
