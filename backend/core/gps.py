#!/usr/bin/env python3
"""
GPS Reader Module
Provides GPS coordinates for violation logging with automatic platform detection.

Features:
- Real GPS support for Raspberry Pi (via gpsd)
- Mock GPS for laptop/desktop development
- Thread-safe location reading
- Automatic fallback to mock mode
"""

import threading
import time
import random
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# Try importing gpsd for Raspberry Pi
try:
    import gpsd
    GPSD_AVAILABLE = True
except ImportError:
    GPSD_AVAILABLE = False
    logger.info("gpsd not available - using mock GPS mode")


# ==============================================
# DATA STRUCTURES
# ==============================================

@dataclass
class GPSLocation:
    """GPS location data"""
    latitude: float
    longitude: float
    accuracy_meters: float
    timestamp: datetime
    is_mock: bool
    altitude: Optional[float] = None
    speed_kmh: Optional[float] = None
    
    def __str__(self):
        mock_indicator = " (MOCK)" if self.is_mock else ""
        return (
            f"GPS{mock_indicator}: {self.latitude:.6f}°N, {self.longitude:.6f}°E "
            f"±{self.accuracy_meters:.1f}m"
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'accuracy_meters': self.accuracy_meters,
            'timestamp': self.timestamp.isoformat(),
            'is_mock': self.is_mock,
            'altitude': self.altitude,
            'speed_kmh': self.speed_kmh,
        }
    
    def get_google_maps_url(self) -> str:
        """Get Google Maps URL for this location"""
        return f"https://maps.google.com/maps?q={self.latitude},{self.longitude}"


# ==============================================
# GPS READER CLASS
# ==============================================

class GPSReader:
    """
    GPS Reader with automatic platform detection.
    
    - Raspberry Pi: Uses real GPS via gpsd
    - Laptop/Desktop: Uses mock GPS with simulated movement
    
    Usage:
        gps = GPSReader()
        gps.start()
        location = gps.get_location()
        print(location)
        gps.stop()
    """
    
    def __init__(
        self,
        mock_center: Tuple[float, float] = (18.5204, 73.8567),  # Pune, India
        mock_radius_km: float = 5.0,
        update_interval: float = 1.0,
    ):
        """
        Initialize GPS reader.
        
        Args:
            mock_center: Center coordinates for mock GPS (lat, lon)
            mock_radius_km: Radius for random movement in mock mode
            update_interval: Seconds between GPS updates
        """
        self.mock_center = mock_center
        self.mock_radius_km = mock_radius_km
        self.update_interval = update_interval
        
        # Detect if we should use real GPS
        self.use_real_gps = self._should_use_real_gps()
        
        # Current location (thread-safe)
        self._location: Optional[GPSLocation] = None
        self._location_lock = threading.Lock()
        
        # Thread control
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        
        # Mock GPS state
        self._mock_lat = mock_center[0]
        self._mock_lon = mock_center[1]
        self._mock_speed = 0.0  # km/h
        self._mock_heading = random.uniform(0, 360)  # degrees
        
        logger.info(
            f"GPS Reader initialized | Mode: {'REAL' if self.use_real_gps else 'MOCK'} | "
            f"Center: {mock_center}"
        )
    
    def _should_use_real_gps(self) -> bool:
        """Detect if real GPS should be used"""
        # Check if gpsd is available
        if not GPSD_AVAILABLE:
            return False
        
        # Check if running on Raspberry Pi
        try:
            device_tree = Path("/proc/device-tree/model")
            if device_tree.exists():
                with open(device_tree, "rb") as f:
                    content = f.read().decode("utf-8", errors="ignore")
                    if "Raspberry Pi" in content:
                        logger.info("Raspberry Pi detected - attempting real GPS")
                        return True
        except Exception:
            pass
        
        return False
    
    def start(self) -> threading.Thread:
        """
        Start GPS reading thread.
        
        Returns:
            Thread object
        """
        if self._thread and self._thread.is_alive():
            logger.warning("GPS thread already running")
            return self._thread
        
        self._stop_event.clear()
        
        if self.use_real_gps:
            self._thread = threading.Thread(
                target=self._real_gps_loop,
                daemon=True,
                name="RealGPSThread"
            )
        else:
            self._thread = threading.Thread(
                target=self._mock_gps_loop,
                daemon=True,
                name="MockGPSThread"
            )
        
        self._thread.start()
        logger.info(f"GPS thread started ({'REAL' if self.use_real_gps else 'MOCK'} mode)")
        
        return self._thread
    
    def stop(self):
        """Stop GPS reading thread"""
        if self._thread and self._thread.is_alive():
            logger.info("Stopping GPS thread...")
            self._stop_event.set()
            self._thread.join(timeout=2.0)
            logger.info("GPS thread stopped")
    
    def get_location(self) -> Optional[GPSLocation]:
        """
        Get current GPS location (thread-safe).
        
        Returns:
            GPSLocation object or None if no fix yet
        """
        with self._location_lock:
            return self._location
    
    def is_ready(self) -> bool:
        """Check if GPS has a valid location"""
        return self._location is not None
    
    # ==============================================
    # REAL GPS (Raspberry Pi)
    # ==============================================
    
    def _real_gps_loop(self):
        """Real GPS reading loop using gpsd"""
        logger.info("Connecting to gpsd...")
        
        try:
            # Connect to gpsd
            gpsd.connect()
            logger.info("✓ Connected to gpsd")
            
            # Wait for first fix
            logger.info("Waiting for GPS fix (this may take 30-90 seconds)...")
            fix_acquired = False
            
            while not self._stop_event.is_set():
                try:
                    # Get GPS packet
                    packet = gpsd.get_current()
                    
                    # Check if we have a valid fix
                    if packet.mode >= 2:  # 2D or 3D fix
                        if not fix_acquired:
                            logger.info("✓ GPS fix acquired!")
                            fix_acquired = True
                        
                        # Create location object
                        location = GPSLocation(
                            latitude=packet.lat,
                            longitude=packet.lon,
                            accuracy_meters=packet.error.get('epx', 2.5),  # Horizontal error
                            timestamp=datetime.now(),
                            is_mock=False,
                            altitude=packet.alt if hasattr(packet, 'alt') else None,
                            speed_kmh=packet.hspeed * 3.6 if hasattr(packet, 'hspeed') else None,  # m/s to km/h
                        )
                        
                        # Update current location (thread-safe)
                        with self._location_lock:
                            self._location = location
                        
                        logger.debug(f"GPS update: {location}")
                    
                    else:
                        if fix_acquired:
                            logger.warning("GPS fix lost")
                            fix_acquired = False
                    
                    # Wait before next update
                    time.sleep(self.update_interval)
                
                except Exception as e:
                    logger.error(f"GPS read error: {e}")
                    time.sleep(self.update_interval)
        
        except Exception as e:
            logger.error(f"Failed to connect to gpsd: {e}")
            logger.info("Falling back to mock GPS mode")
            # Fall back to mock GPS
            self._mock_gps_loop()
    
    # ==============================================
    # MOCK GPS (Laptop/Desktop)
    # ==============================================
    
    def _mock_gps_loop(self):
        """Mock GPS loop with simulated movement"""
        logger.info("Starting mock GPS with simulated movement")
        logger.warning("⚠️ MOCK GPS MODE - For development only, not for production!")
        
        while not self._stop_event.is_set():
            try:
                # Simulate vehicle movement
                self._update_mock_position()
                
                # Create mock location
                location = GPSLocation(
                    latitude=self._mock_lat,
                    longitude=self._mock_lon,
                    accuracy_meters=0.0,  # Perfect accuracy in mock mode
                    timestamp=datetime.now(),
                    is_mock=True,
                    altitude=None,
                    speed_kmh=self._mock_speed,
                )
                
                # Update current location (thread-safe)
                with self._location_lock:
                    self._location = location
                
                logger.debug(f"Mock GPS update: {location}")
                
                # Wait before next update
                time.sleep(self.update_interval)
            
            except Exception as e:
                logger.error(f"Mock GPS error: {e}")
                time.sleep(self.update_interval)
    
    def _update_mock_position(self):
        """Update mock GPS position with simulated movement"""
        # Simulate random walk within radius
        # 1 degree ≈ 111 km at equator
        
        # Random speed change (0-60 km/h)
        self._mock_speed += random.uniform(-5, 5)
        self._mock_speed = max(0, min(60, self._mock_speed))
        
        # Random heading change
        self._mock_heading += random.uniform(-15, 15)
        self._mock_heading = self._mock_heading % 360
        
        # Calculate movement (speed in km/h, time in seconds)
        distance_km = (self._mock_speed / 3600) * self.update_interval
        
        # Convert to degrees (approximate)
        import math
        distance_deg = distance_km / 111.0
        
        # Update position
        self._mock_lat += distance_deg * math.cos(math.radians(self._mock_heading))
        self._mock_lon += distance_deg * math.sin(math.radians(self._mock_heading))
        
        # Keep within radius of center
        center_lat, center_lon = self.mock_center
        dist_from_center = math.sqrt(
            (self._mock_lat - center_lat)**2 + (self._mock_lon - center_lon)**2
        ) * 111.0  # Convert to km
        
        if dist_from_center > self.mock_radius_km:
            # Bounce back toward center
            self._mock_heading = math.degrees(
                math.atan2(center_lon - self._mock_lon, center_lat - self._mock_lat)
            )


# ==============================================
# UTILITY FUNCTIONS
# ==============================================

def get_google_maps_url(lat: float, lon: float) -> str:
    """Get Google Maps URL for coordinates"""
    return f"https://maps.google.com/maps?q={lat},{lon}"


def calculate_distance_km(
    lat1: float, lon1: float,
    lat2: float, lon2: float
) -> float:
    """
    Calculate distance between two GPS coordinates using Haversine formula.
    
    Args:
        lat1, lon1: First coordinate
        lat2, lon2: Second coordinate
    
    Returns:
        Distance in kilometers
    """
    import math
    
    # Earth radius in km
    R = 6371.0
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    distance = R * c
    return distance


# ==============================================
# MAIN / TESTING
# ==============================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("GPS Reader Test")
    print("=" * 60)
    
    # Create GPS reader
    gps = GPSReader(
        mock_center=(18.5204, 73.8567),  # Pune
        mock_radius_km=5.0,
        update_interval=1.0,
    )
    
    # Start reading
    gps.start()
    
    print("\nReading GPS for 10 seconds...\n")
    
    try:
        for i in range(10):
            time.sleep(1)
            location = gps.get_location()
            
            if location:
                print(f"[{i+1}/10] {location}")
                print(f"        Maps: {location.get_google_maps_url()}")
            else:
                print(f"[{i+1}/10] Waiting for GPS fix...")
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    finally:
        gps.stop()
        print("\n" + "=" * 60)
        print("GPS Reader test complete")
        print("=" * 60)
