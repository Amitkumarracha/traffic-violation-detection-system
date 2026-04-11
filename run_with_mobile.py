#!/usr/bin/env python3
"""
Run Traffic Violation Detection with Mobile Camera
Simplified launcher for mobile camera integration
"""

import argparse
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    parser = argparse.ArgumentParser(
        description="Run traffic violation detection with mobile camera"
    )
    parser.add_argument(
        "--source",
        type=int,
        default=0,
        help="Camera source (0=built-in, 1=external)"
    )
    parser.add_argument(
        "--ip",
        type=str,
        help="IP Webcam address (e.g., 192.168.1.100:8080)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="API server host (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="API server port (default: 8000)"
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Run without display (headless mode for RPi)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  TRAFFIC VIOLATION DETECTION - MOBILE CAMERA")
    print("=" * 60)
    
    # Determine camera source
    if args.ip:
        camera_source = f"http://{args.ip}/video"
        print(f"\n📱 Using IP Webcam: {args.ip}")
    else:
        camera_source = args.source
        print(f"\n📷 Using camera source: {args.source}")
    
    print(f"🌐 API Server: http://{args.host}:{args.port}")
    print(f"📊 Display: {'Disabled (headless)' if args.no_display else 'Enabled'}")
    
    # Set environment variables
    os.environ['CAMERA_SOURCE'] = str(camera_source)
    os.environ['API_HOST'] = args.host
    os.environ['API_PORT'] = str(args.port)
    os.environ['NO_DISPLAY'] = '1' if args.no_display else '0'
    
    print("\n🚀 Starting system...")
    print("   Press Ctrl+C to stop\n")
    
    # Import and run server
    try:
        from backend.api import app
        import uvicorn
        
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level="info"
        )
    
    except KeyboardInterrupt:
        print("\n\n✅ System stopped by user")
        return 0
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check if dependencies are installed:")
        print("     pip install -r backend_requirements.txt")
        print("  2. Check if model exists:")
        print("     ls model/checkpoints/best.pt")
        print("  3. Check if camera is accessible:")
        print("     python test_mobile_camera.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())
