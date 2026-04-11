"""
Backend API package - FastAPI application and routes.
"""

from backend.api.app import app, manager, broadcast_violation, broadcast_stats_update

__all__ = [
    'app',
    'manager',
    'broadcast_violation',
    'broadcast_stats_update',
]
