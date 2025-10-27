#!/usr/bin/env python3
"""
Batch upload script for multiple songs.
Reads metadata from filenames or ID3 tags.
"""

import os
import sys
import requests
from pathlib import Path
import time

# Try to import mutagen for ID3 tag reading (optional)
try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3NoHeaderError
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False
    print("Note: Install 'mutagen' for automatic metadata extraction: pip install mutagen")

def extract_metadata_from_filename(file_path):
    """Extract metadata from filename patterns like 'Artist - Title.mp3'"""
    name = file_path.stem
    
    # Try different patterns
    if ' - ' in name:
        parts = name.split(' - ', 1)
        return parts[0].strip(), parts[1].strip(), ""
    else:
        return "Unknown Artist", name, ""

def extract_metadata_from_tags(file_path):
    """Extract metadata from ID3 tags if mutagen is available"""
    if not HAS_MUTAGEN:
        return extract_metadata_from_filename(file_path)
    
    try:
        audio = MP3(file_path)
        
        title = str(audio.get('TIT2', [''])[0]) if 'TIT2' in audio else ""
        artist = str(audio.get('TPE1', [''])[0]) if 'TPE1' in audio else ""
        album = str(audio.get('TALB', [''])[0]) if 'TALB' in audio else ""
        
        # Fallback to filename if tags are empty
        if not title or not artist:
            f_artist, f_title, f_album = extract_metadata_from_filename(file_path)
            title = title or f_title
            artist = artist or f_artist
            album = album or f_album
            
        return artist, title, album
        
    except (ID3NoHeaderError, Exception):
        return extract_metadata_from_filename(file_path)

def upload_song(file_path, title, artist, album="", server_url="http://localhost:8000"):
    """Upload a single song"""
    try:
        with open(file_path, 'rb') as audio_file:
            files = {
                'audio': (file_path.name, audio_file, 'audio/mpeg')
            }
            data = {
                'title': title,
                'artist': artist,
                'album': album
            }
            
            response = requests.post(
                f"{server_url}/api/v1/upload",
                files=files,
                data=data,
                timeout=60
            )
        
        return response.status_code == 200, response
        
    except Exception as e:
        return False, str(e)

def batch_upload(directory, server_url="http://localhost:8000"):
    """Upload all MP3 files in a directory"""
    directory = Path(directory)
    
    if not directory.exists():
        print(f"Error: Directory '{directory}' not found!")
        return
    
    # Find all MP3 files
    mp3_files = list(directory.glob("*.mp3")) + list(directory.glob("*.MP3"))
    
    if not mp3_files:
        print(f"No MP3 files found in '{directory}'")
        return
    
    print(f"Found {len(mp3_files)} MP3 files to upload")
    print(f"Server: {server_url}")
    print("=" * 60)
    
    successful = 0
    failed = 0
    
    for i, file_path in enumerate(mp3_files, 1):
        print(f"\n[{i}/{len(mp3_files)}] Processing: {file_path.name}")
        
        # Extract metadata
        artist, title, album = extract_metadata_from_tags(file_path)
        
        print(f"  Title: {title}")
        print(f"  Artist: {artist}")
        print(f"  Album: {album}")
        
        # Upload
        success, response = upload_song(file_path, title, artist, album, server_url)
        
        if success:
            print("  ✅ Upload successful!")
            successful += 1
        else:
            print(f"  ❌ Upload failed: {response}")
            failed += 1
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print(f"Upload complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python batch_upload.py <directory>")
        print("\nExample:")
        print("python batch_upload.py /path/to/music/folder")
        sys.exit(1)
    
    directory = sys.argv[1]
    batch_upload(directory)

if __name__ == "__main__":
    main()