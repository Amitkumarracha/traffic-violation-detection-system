#!/usr/bin/env python3
"""
Test Mobile Camera Connection
Quick script to test if mobile camera is accessible
"""

import cv2
import argparse
import sys

def test_camera(source):
    """Test camera connection and display feed"""
    
    print(f"\n🎥 Testing camera source: {source}")
    print("Press 'q' to quit\n")
    
    # Try to open camera
    cap = cv2.VideoCapture(source)
    
    if not cap.isOpened():
        print(f"❌ Failed to open camera: {source}")
        print("\nTroubleshooting:")
        print("  - Check if camera is connected")
        print("  - Try different source numbers (0, 1, 2)")
        print("  - For IP Webcam: use --ip flag with IP:PORT")
        return False
    
    print("✅ Camera opened successfully!")
    
    # Get camera properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"Resolution: {width}x{height}")
    print(f"FPS: {fps:.1f}")
    print("\nDisplaying feed... Press 'q' to quit")
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("❌ Failed to read frame")
            break
        
        frame_count += 1
        
        # Add info overlay
        cv2.putText(frame, f"Frame: {frame_count}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, "Press 'q' to quit", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Display
        cv2.imshow('Mobile Camera Test', frame)
        
        # Check for quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"\n✅ Test complete! Captured {frame_count} frames")
    return True


def test_ip_webcam(ip_address):
    """Test IP Webcam connection"""
    
    # IP Webcam URL format
    url = f"http://{ip_address}/video"
    
    print(f"\n🎥 Testing IP Webcam: {url}")
    print("Make sure IP Webcam app is running on your phone\n")
    
    return test_camera(url)


def main():
    parser = argparse.ArgumentParser(description="Test mobile camera connection")
    parser.add_argument(
        "--source",
        type=int,
        default=0,
        help="Camera source (0=built-in, 1=external, 2=USB)"
    )
    parser.add_argument(
        "--ip",
        type=str,
        help="IP Webcam address (e.g., 192.168.1.100:8080)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  MOBILE CAMERA TEST")
    print("=" * 60)
    
    if args.ip:
        success = test_ip_webcam(args.ip)
    else:
        success = test_camera(args.source)
    
    if success:
        print("\n✅ Camera is working! You can now run the full system.")
        print("\nNext steps:")
        print("  python run_with_mobile.py")
        return 0
    else:
        print("\n❌ Camera test failed. Check troubleshooting tips above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
