#!/usr/bin/env python3
"""
Simple script to upload songs to the audio fingerprinting database.
Usage: python upload_song.py path/to/song.mp3 "Song Title" "Artist Name" "Album Name"
"""

import sys
import requests
from pathlib import Path

def upload_song(file_path, title, artist, album="", server_url="http://localhost:8000"):
    """Upload a song to the audio fingerprinting server."""
    
    file_path = Path(file_path)
    if not file_path.exists():
        print(f"Error: File '{file_path}' not found!")
        return False
    
    print(f"Uploading: {file_path.name}")
    print(f"Title: {title}")
    print(f"Artist: {artist}")
    print(f"Album: {album}")
    print(f"Server: {server_url}")
    print("-" * 50)
    
    try:
        # Prepare the files and data for upload
        with open(file_path, 'rb') as audio_file:
            files = {
                'audio': (file_path.name, audio_file, 'audio/mpeg')
            }
            data = {
                'title': title,
                'artist': artist,
                'album': album
            }
            
            # Make the upload request
            response = requests.post(
                f"{server_url}/api/v1/upload",
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload successful!")
            print(f"Song ID: {result.get('song_id', 'N/A')}")
            print(f"Fingerprints generated: {result.get('fingerprint_count', 'N/A')}")
            return True
        else:
            print(f"❌ Upload failed!")
            print(f"Status code: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server!")
        print("Make sure the backend server is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    if len(sys.argv) < 4:
        print("Usage: python upload_song.py <file_path> <title> <artist> [album]")
        print("\nExample:")
        print('python upload_song.py "song.mp3" "Bohemian Rhapsody" "Queen" "A Night at the Opera"')
        sys.exit(1)
    
    file_path = sys.argv[1]
    title = sys.argv[2]
    artist = sys.argv[3]
    album = sys.argv[4] if len(sys.argv) > 4 else ""
    
    success = upload_song(file_path, title, artist, album)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()