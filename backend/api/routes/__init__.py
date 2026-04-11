"""
API routes package - exports all routers.
"""

from backend.api.routes.violations import router as violations_router
from backend.api.routes.fraud import router as fraud_router
from backend.api.routes.health import router as health_router

__all__ = [
    'violations_router',
    'fraud_router',
    'health_router',
]
