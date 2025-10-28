#!/usr/bin/env python3
"""
Test script to check what endpoints are available on the server.
"""

import requests
import json

def test_endpoints():
    base_url = "http://localhost:8000"
    
    endpoints_to_test = [
        "/",
        "/docs",
        "/health",
        "/api/v1/health",
        "/api/v1/upload",
        "/api/v1/identify",
    ]
    
    print("Testing server endpoints...")
    print("=" * 50)
    
    for endpoint in endpoints_to_test:
        url = base_url + endpoint
        try:
            response = requests.get(url, timeout=5)
            print(f"GET {endpoint}: {response.status_code} - {response.text[:100]}")
        except requests.exceptions.RequestException as e:
            print(f"GET {endpoint}: ERROR - {e}")
    
    print("\n" + "=" * 50)
    print("Testing POST to upload endpoint...")
    
    # Test POST to upload endpoint
    try:
        # Create a small test file
        test_data = {
            'title': 'Test Song',
            'artist': 'Test Artist',
            'album': 'Test Album'
        }
        
        response = requests.post(f"{base_url}/api/v1/upload", data=test_data, timeout=5)
        print(f"POST /api/v1/upload: {response.status_code} - {response.text}")
        
    except requests.exceptions.RequestException as e:
        print(f"POST /api/v1/upload: ERROR - {e}")

if __name__ == "__main__":
    test_endpoints()