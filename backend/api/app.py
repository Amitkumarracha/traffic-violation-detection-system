"""
FastAPI application - serves React dashboard and external API consumers.

Endpoints:
- GET  /api/violations               - List violations (paginated)
- GET  /api/violations/{id}          - Get single violation
- GET  /api/violations/stats/overview- Violation statistics
- GET  /api/violations/{id}/image    - Serve evidence image
- POST /api/violations/{id}/verify   - Trigger LLM verification

- POST /api/fraud/check              - Perform fraud investigation
- GET  /api/fraud/checks             - List fraud checks

- GET  /api/health/                  - Full health check
- GET  /api/health/live              - Lightweight health check
- GET  /api/health/db                - Database health check

- GET  /docs                         - Swagger UI (auto-generated)
- GET  /redoc                        - ReDoc documentation

- WS   /ws/live                      - WebSocket for live violations
"""

import logging
import asyncio
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse

from backend.database import startup as db_startup, shutdown as db_shutdown
from backend.api.routes import (
    violations_router,
    fraud_router,
    health_router,
)

logger = logging.getLogger(__name__)


# =====================
# Serve Frontend
# =====================

def serve_frontend(app: FastAPI):
    """Serve the frontend HTML"""
    frontend_path = Path(__file__).parent.parent.parent / "frontend"
    
    if frontend_path.exists():
        # Serve static files
        app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
        
        # Serve index.html at root
        @app.get("/")
        async def read_root():
            index_file = frontend_path / "index.html"
            if index_file.exists():
                return FileResponse(index_file)
            return {"message": "Frontend not found"}
    else:
        logger.warning(f"Frontend directory not found: {frontend_path}")


# =====================
# WebSocket Manager
# =====================

class ConnectionManager:
    """Manage WebSocket connections for live violation streaming."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Active: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Active: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all active connections."""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send message to specific connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)


manager = ConnectionManager()


# =====================
# Startup & Shutdown
# =====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events."""
    
    # STARTUP
    logger.info("=" * 60)
    logger.info("🚀 Starting Traffic Violation Detection API")
    logger.info("=" * 60)
    
    try:
        # Initialize database
        logger.info("📁 Initializing database...")
        db_startup()
        logger.info("✓ Database initialized")
        
        logger.info("✓ API startup complete")
        logger.info("📊 Swagger UI: http://localhost:8000/docs")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"✗ Startup error: {e}")
        raise
    
    yield
    
    # SHUTDOWN
    logger.info("=" * 60)
    logger.info("🛑 Shutting down API")
    logger.info("=" * 60)
    
    try:
        # Close database connections
        logger.info("📁 Shutting down database...")
        db_shutdown()
        logger.info("✓ Database shutdown")
        
        # Close WebSocket connections
        for ws in manager.active_connections[:]:
            await ws.close()
        
        logger.info("✓ API shutdown complete")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"✗ Shutdown error: {e}")


# =====================
# FastAPI App Creation
# =====================

app = FastAPI(
    title="Traffic Violation Detection API",
    description="API for detecting and managing traffic violations with fraud detection",
    version="1.0.0",
    lifespan=lifespan,
)


# =====================
# CORS Middleware
# =====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================
# Serve Frontend
# =====================

serve_frontend(app)

# =====================
# Include Routers
# =====================

app.include_router(violations_router)
app.include_router(fraud_router)
app.include_router(health_router)


# =====================
# WebSocket Endpoints
# =====================

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for live violation streaming.
    
    Streams real-time violations as they're detected by the pipeline.
    
    **Message Format:**
    ```json
    {
        "event_type": "violation_detected",
        "violation_id": 123,
        "violation_type": "without_helmet",
        "confidence": 0.95,
        "timestamp": "2026-03-31T10:30:00Z",
        "plate_number": "MH12AB1234",
        "latitude": 18.5204,
        "longitude": 73.8567,
        "image_url": "/api/violations/123/image",
        "platform": "laptop_cpu"
    }
    ```
    
    **Usage (JavaScript):**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/live');
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('New violation:', data);
    };
    ```
    """
    await manager.connect(websocket)
    
    try:
        # Keep connection open and listen for messages
        while True:
            # Receive any messages from client (for keep-alive or commands)
            data = await websocket.receive_text()
            
            # Handle client commands if needed
            if data == "ping":
                await manager.send_personal(websocket, {"type": "pong"})
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# =====================
# Root Endpoints
# =====================

@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": "Traffic Violation Detection API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "websocket": "ws://localhost:8000/ws/live",
        "endpoints": {
            "violations": "/api/violations",
            "fraud": "/api/fraud",
            "health": "/api/health",
        },
    }


@app.get("/api")
async def api_root():
    """API root - lists available endpoints."""
    return {
        "violations": {
            "list": "GET /api/violations",
            "get": "GET /api/violations/{id}",
            "stats": "GET /api/violations/stats/overview",
            "image": "GET /api/violations/{id}/image",
            "verify": "POST /api/violations/{id}/verify",
        },
        "fraud": {
            "check": "POST /api/fraud/check",
            "list": "GET /api/fraud/checks",
        },
        "health": {
            "full": "GET /api/health/",
            "live": "GET /api/health/live",
            "db": "GET /api/health/db",
        },
    }


# =====================
# Error Handlers
# =====================

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
        },
    )


# =====================
# Helper Functions
# =====================

async def broadcast_violation(violation_dict: dict):
    """Broadcast a violation event to all connected WebSocket clients."""
    message = {
        "event_type": "violation_detected",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **violation_dict,
    }
    await manager.broadcast(message)


async def broadcast_stats_update(stats_dict: dict):
    """Broadcast a stats update to all connected WebSocket clients."""
    message = {
        "event_type": "stats_update",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **stats_dict,
    }
    await manager.broadcast(message)


# =====================
# Logging Configuration
# =====================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)


if __name__ == "__main__":
    import uvicorn
    
    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
