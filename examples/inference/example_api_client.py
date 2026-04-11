#!/usr/bin/env python3
"""
Example client demonstrating all Traffic Violation Detection API endpoints.

Run the server first:
    python backend/run_server.py

Then run this script:
    python example_api_client.py
"""

import requests
import json
import asyncio
import websockets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any


# API Configuration
API_BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/live"


class APIClient:
    """Client for Traffic Violation Detection API."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def list_violations(self, skip: int = 0, limit: int = 10, **filters) -> Dict[str, Any]:
        """List violations with pagination and filters."""
        params = {"skip": skip, "limit": limit}
        params.update(filters)
        
        response = self.session.get(f"{self.base_url}/api/violations", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_violation(self, violation_id: int) -> Dict[str, Any]:
        """Get single violation details."""
        response = self.session.get(f"{self.base_url}/api/violations/{violation_id}")
        response.raise_for_status()
        return response.json()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get violation statistics."""
        response = self.session.get(f"{self.base_url}/api/violations/stats/overview")
        response.raise_for_status()
        return response.json()
    
    def get_violation_image(self, violation_id: int, save_path: str = None) -> bytes:
        """Download violation evidence image."""
        response = self.session.get(f"{self.base_url}/api/violations/{violation_id}/image")
        response.raise_for_status()
        
        if save_path:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"✓ Image saved to {save_path}")
        
        return response.content
    
    def verify_violation(self, violation_id: int, use_gemini: bool = True) -> Dict[str, Any]:
        """Trigger LLM verification for a violation."""
        data = {
            "use_gemini": use_gemini,
            "reprocess": False
        }
        
        response = self.session.post(
            f"{self.base_url}/api/violations/{violation_id}/verify",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def check_fraud(
        self,
        claim_timestamp: datetime,
        latitude: float,
        longitude: float,
        plate_number: str = None,
        claim_description: str = None,
        search_radius_meters: int = 200
    ) -> Dict[str, Any]:
        """Check for potential fraud."""
        data = {
            "claim_timestamp": claim_timestamp.isoformat(),
            "latitude": latitude,
            "longitude": longitude,
            "claim_description": claim_description or "Violation is false",
            "search_radius_meters": search_radius_meters,
        }
        
        if plate_number:
            data["plate_number"] = plate_number
        
        response = self.session.post(f"{self.base_url}/api/fraud/check", json=data)
        response.raise_for_status()
        return response.json()
    
    def get_fraud_checks(self) -> list:
        """Get recent fraud checks."""
        response = self.session.get(f"{self.base_url}/api/fraud/checks")
        response.raise_for_status()
        return response.json()
    
    def get_health(self) -> Dict[str, Any]:
        """Get system health status."""
        response = self.session.get(f"{self.base_url}/api/health/")
        response.raise_for_status()
        return response.json()
    
    def get_health_live(self) -> Dict[str, Any]:
        """Get lightweight health status."""
        response = self.session.get(f"{self.base_url}/api/health/live")
        response.raise_for_status()
        return response.json()
    
    def get_db_health(self) -> Dict[str, Any]:
        """Get database health status."""
        response = self.session.get(f"{self.base_url}/api/health/db")
        response.raise_for_status()
        return response.json()


async def websocket_example():
    """Example of connecting to WebSocket for live violations."""
    print("\n" + "=" * 60)
    print("WebSocket Example - Live Violations")
    print("=" * 60)
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("✓ Connected to WebSocket")
            print("Listening for violations (Ctrl+C to exit)...\n")
            
            # Listen for messages for 30 seconds
            import time
            start_time = time.time()
            
            while time.time() - start_time < 30:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    
                    print(f"📌 {data.get('event_type', 'unknown')}")
                    if data.get('violation_type'):
                        print(f"   Type: {data['violation_type']}")
                        print(f"   Confidence: {data.get('confidence', 'N/A'):.2f}")
                        print(f"   Plate: {data.get('plate_number', 'Not detected')}")
                        print()
                
                except asyncio.TimeoutError:
                    pass
    
    except Exception as e:
        print(f"✗ WebSocket error: {e}")


def main():
    """Run example API calls."""
    
    print("\n" + "=" * 60)
    print("Traffic Violation Detection - API Client Examples")
    print("=" * 60)
    
    client = APIClient()
    
    # 1. Health Check
    print("\n1. System Health Check")
    print("-" * 60)
    try:
        health = client.get_health()
        print(f"Status: {health['status']}")
        print(f"Platform: {health['platform']}")
        print(f"DB Connected: {health['db_connection']}")
        print(f"Violations Today: {health['violations_today']}")
        print(f"Memory Usage: {health['memory_usage_mb']:.1f} MB")
        print(f"Uptime: {health['uptime_seconds']:.1f}s")
    except requests.exceptions.ConnectionError:
        print("✗ Connection refused - is the server running?")
        print("  Start server with: python backend/run_server.py")
        return
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # 2. List Violations
    print("\n2. List Recent Violations")
    print("-" * 60)
    try:
        result = client.list_violations(limit=5)
        print(f"Total violations: {result['total']}")
        print(f"Showing {len(result['violations'])} violations:\n")
        
        for v in result['violations'][:3]:
            print(f"  ID: {v['id']}")
            print(f"  Type: {v['violation_type']}")
            print(f"  Plate: {v['plate_number'] or 'Not detected'}")
            print(f"  Confidence: {v['confidence']:.2f}")
            print(f"  Time: {v['timestamp']}")
            print()
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # 3. Get Statistics
    print("\n3. Violation Statistics")
    print("-" * 60)
    try:
        stats = client.get_stats()
        print(f"Total violations: {stats['total_count']}")
        print(f"Today: {stats['today_count']}")
        print(f"Synced: {stats['synced_count']}")
        print(f"Unsynced: {stats['unsynced_count']}")
        print(f"Avg confidence: {stats['avg_confidence']:.2f}")
        print(f"Plate detection rate: {stats['plate_detection_rate']:.1f}%")
        
        print(f"\nBy violation type:")
        for vtype, count in stats['by_type'].items():
            print(f"  {vtype}: {count}")
        
        print(f"\nBy platform:")
        for platform, count in stats['by_platform'].items():
            print(f"  {platform}: {count}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # 4. Fraud Check Example
    print("\n4. Fraud Check Example")
    print("-" * 60)
    try:
        # Check violations from 1 hour ago
        claim_time = datetime.now(timezone.utc) - timedelta(hours=1)
        
        fraud_result = client.check_fraud(
            claim_timestamp=claim_time,
            latitude=18.5204,
            longitude=73.8567,
            plate_number="MH12AB1234",
            claim_description="I was not riding at this location",
            search_radius_meters=200
        )
        
        print(f"Check ID: {fraud_result['check_id']}")
        print(f"Footage found: {fraud_result['footage_found']}")
        print(f"Footage count: {fraud_result['footage_count']}")
        print(f"Fraud score: {fraud_result['fraud_score']:.2f}")
        print(f"Severity: {fraud_result['fraud_severity']}")
        print(f"Recommendation: {fraud_result['recommendation']}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # 5. Get specific violation
    print("\n5. Get Single Violation Details")
    print("-" * 60)
    try:
        # Get the first violation if available
        result = client.list_violations(limit=1)
        if result['violations']:
            v = result['violations'][0]
            violation = client.get_violation(v['id'])
            
            print(f"ID: {violation['id']}")
            print(f"Type: {violation['violation_type']}")
            print(f"Confidence: {violation['confidence']:.2f}")
            print(f"Plate: {violation['plate_number']}")
            print(f"Location: ({violation['latitude']}, {violation['longitude']})")
            print(f"LLM Verified: {violation['llm_verified']}")
            print(f"Platform: {violation['platform']}")
        else:
            print("No violations available")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # 6. Database Health
    print("\n6. Database Status")
    print("-" * 60)
    try:
        db_health = client.get_db_health()
        print(f"Connected: {db_health['connected']}")
        print(f"Total violations: {db_health['total_violations']}")
        print(f"Recent violations: {db_health['recent_violations_count']}")
        print(f"Last violation: {db_health['last_violation_timestamp']}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # 7. WebSocket Example (async)
    print("\n7. WebSocket Live Feed")
    print("-" * 60)
    try:
        asyncio.run(websocket_example())
    except KeyboardInterrupt:
        print("\nWebSocket example interrupted")
    except Exception as e:
        print(f"✗ WebSocket error: {e}")
    
    print("\n" + "=" * 60)
    print("✓ Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
