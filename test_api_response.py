#!/usr/bin/env python3
"""Test the API response format."""

import requests
import json

def test_api():
    """Test the API endpoint."""
    try:
        # Create a small dummy audio file
        dummy_audio = b'\x00' * 1000  # 1KB of silence
        
        files = {'audio_file': ('test.wav', dummy_audio, 'audio/wav')}
        
        response = requests.post('http://localhost:8000/api/v1/identify', files=files)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body:")
        print(response.text)
        
        if response.headers.get('content-type', '').startswith('application/json'):
            try:
                json_data = response.json()
                print(f"\nParsed JSON:")
                print(json.dumps(json_data, indent=2))
            except:
                print("Failed to parse as JSON")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()