#!/usr/bin/env python3
"""
Run the FastAPI server for Traffic Violation Detection.

Usage:
    python backend/run_server.py              # Development (reload on changes)
    python backend/run_server.py --prod        # Production
    python backend/run_server.py --host 0.0.0.0 --port 8000
"""

import sys
import argparse
import uvicorn

from backend.api import app


def main():
    """Run the FastAPI server."""
    parser = argparse.ArgumentParser(
        description="Run Traffic Violation Detection API server"
    )
    parser.add_argument(
        "--prod",
        action="store_true",
        help="Production mode (no reload)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Server host (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server port (default: 8000)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of workers (default: 1)"
    )
    
    args = parser.parse_args()
    
    # Run server
    if args.prod:
        # Production: no reload
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            workers=args.workers,
            log_level="info",
        )
    else:
        # Development: auto-reload on file changes
        uvicorn.run(
            "backend.api:app",
            host=args.host,
            port=args.port,
            reload=True,
            log_level="info",
        )


if __name__ == "__main__":
    main()
