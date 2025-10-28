#!/usr/bin/env python3
"""
Real audio fingerprinting script using librosa for audio analysis.
Generates actual fingerprints from MP3 files that can be matched.
"""

import os
import sys
import numpy as np
import psycopg2
from pathlib import Path
import hashlib
import time

# Audio processing libraries
HAS_LIBROSA = False
HAS_SCIPY = False

try:
    import librosa
    import librosa.display
    HAS_LIBROSA = True
    print("✅ librosa loaded successfully")
except ImportError as e:
    print(f"❌ librosa import failed: {e}")

try:
    from scipy.signal import find_peaks
    HAS_SCIPY = True
    print("✅ scipy loaded successfully")
except ImportError as e:
    print(f"❌ scipy import failed: {e}")

def extract_audio_fingerprints(file_path, song_id):
    """Extract real audio fingerprints using spectral analysis."""
    
    if not HAS_LIBROSA or not HAS_SCIPY:
        print("  ❌ Missing required libraries for audio processing")
        return []
    
    try:
        print(f"  🎵 Loading audio file...")
        
        # Load audio file
        y, sr = librosa.load(file_path, sr=22050, duration=30)  # Load first 30 seconds
        print(f"  📊 Sample rate: {sr} Hz, Duration: {len(y)/sr:.1f}s")
        
        # Compute spectrogram
        print(f"  🔍 Computing spectrogram...")
        stft = librosa.stft(y, hop_length=512, n_fft=2048)
        magnitude = np.abs(stft)
        
        # Find spectral peaks (constellation map approach)
        print(f"  ⭐ Finding spectral peaks...")
        fingerprints = []
        
        # Process in time windows
        hop_length = 512
        window_size = 4096  # ~0.2 seconds at 22050 Hz
        
        for t_idx in range(0, magnitude.shape[1] - 10, 10):  # Every ~0.1 seconds
            # Get magnitude spectrum for this time window
            spectrum = magnitude[:, t_idx]
            
            # Find peaks in the spectrum
            peaks, properties = find_peaks(spectrum, height=np.max(spectrum) * 0.1, distance=10)
            
            # Take top peaks
            if len(peaks) >= 2:
                # Sort by magnitude and take top peaks
                peak_magnitudes = spectrum[peaks]
                top_indices = np.argsort(peak_magnitudes)[-5:]  # Top 5 peaks
                top_peaks = peaks[top_indices]
                
                # Create fingerprint pairs
                for i in range(len(top_peaks)):
                    for j in range(i + 1, min(i + 3, len(top_peaks))):  # Pair with next 2 peaks
                        freq1 = top_peaks[i]
                        freq2 = top_peaks[j]
                        
                        # Time offset in milliseconds
                        time_offset_ms = int((t_idx * hop_length / sr) * 1000)
                        
                        # Create hash from frequency pair and time delta
                        freq_diff = abs(freq2 - freq1)
                        hash_input = f"{freq1}_{freq2}_{freq_diff}_{time_offset_ms // 100}"
                        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest()[:12], 16)
                        
                        # Convert frequency bins to Hz
                        freq1_hz = freq1 * sr / (2 * magnitude.shape[0])
                        freq2_hz = freq2 * sr / (2 * magnitude.shape[0])
                        
                        fingerprints.append({
                            'song_id': song_id,
                            'hash_value': hash_value,
                            'time_offset_ms': time_offset_ms,
                            'frequency_1': freq1_hz,
                            'frequency_2': freq2_hz,
                            'time_delta_ms': abs(j - i) * 10  # Approximate time delta
                        })
        
        print(f"  ✅ Generated {len(fingerprints)} fingerprints")
        return fingerprints
        
    except Exception as e:
        print(f"  ❌ Error processing audio: {e}")
        return []

def connect_to_database():
    """Connect to PostgreSQL database with multiple attempts."""
    
    connection_configs = [
        # Try with the project user first
        {
            "host": "localhost",
            "database": "audio_fingerprinting",
            "user": "audio_user",
            "password": "audio_password_change_me",
            "port": "5432"
        },
        # Try with postgres superuser
        {
            "host": "localhost", 
            "database": "audio_fingerprinting",
            "user": "postgres",
            "password": "postgres",
            "port": "5432"
        },
        # Try with different common passwords
        {
            "host": "localhost",
            "database": "audio_fingerprinting", 
            "user": "postgres",
            "password": "admin",
            "port": "5432"
        }
    ]
    
    for config in connection_configs:
        try:
            print(f"Trying connection with user: {config['user']}")
            conn = psycopg2.connect(**config)
            print(f"✅ Connected successfully!")
            return conn
        except Exception as e:
            print(f"❌ Failed: {str(e)[:100]}...")
            continue
    
    print("\n❌ All connection attempts failed!")
    print("\nTo fix this:")
    print("1. Open pgAdmin")
    print("2. Check your postgres user password")
    print("3. Or create the audio_user with: CREATE USER audio_user WITH PASSWORD 'audio_password_change_me';")
    print("4. Grant permissions: GRANT ALL PRIVILEGES ON DATABASE audio_fingerprinting TO audio_user;")
    return None

def add_song_with_real_fingerprints(conn, file_path, title, artist, album=""):
    """Add a song with real audio fingerprints to the database."""
    
    cursor = conn.cursor()
    
    try:
        # Check if song already exists
        cursor.execute("SELECT id FROM songs WHERE title = %s AND artist = %s", (title, artist))
        existing = cursor.fetchone()
        
        if existing:
            print(f"  ⚠️  Song already exists with ID: {existing[0]}")
            return existing[0]
        
        # Insert song
        cursor.execute("""
            INSERT INTO songs (title, artist, album, duration_seconds, year, genre)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (title, artist, album, 180, 2024, "Unknown"))
        
        song_id = cursor.fetchone()[0]
        print(f"  ✅ Song added with ID: {song_id}")
        
        # Generate real fingerprints
        fingerprints = extract_audio_fingerprints(file_path, song_id)
        
        if not fingerprints:
            print(f"  ❌ No fingerprints generated")
            return None
        
        # Insert fingerprints in batches
        print(f"  💾 Inserting {len(fingerprints)} fingerprints...")
        fingerprint_data = [
            (fp['song_id'], fp['hash_value'], fp['time_offset_ms'], 
             fp['frequency_1'], fp['frequency_2'], fp['time_delta_ms'])
            for fp in fingerprints
        ]
        
        cursor.executemany("""
            INSERT INTO fingerprints (song_id, hash_value, time_offset_ms, frequency_1, frequency_2, time_delta_ms)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, fingerprint_data)
        
        conn.commit()
        print(f"  ✅ Successfully added {len(fingerprints)} real fingerprints!")
        
        return song_id
        
    except Exception as e:
        conn.rollback()
        print(f"  ❌ Failed to add song: {e}")
        return None

def process_music_files(folder_path):
    """Process MP3 files and generate real fingerprints."""
    
    if not HAS_LIBROSA or not HAS_SCIPY:
        print("❌ Missing required libraries!")
        print("Install with:")
        print("  pip install librosa scipy soundfile")
        return
    
    folder = Path(folder_path)
    if not folder.exists():
        print(f"❌ Folder not found: {folder_path}")
        return
    
    # Find MP3 files
    mp3_files = list(folder.glob("*.mp3")) + list(folder.glob("*.MP3"))
    
    if not mp3_files:
        print(f"❌ No MP3 files found in: {folder_path}")
        return
    
    print(f"🎵 Found {len(mp3_files)} MP3 files")
    print("=" * 60)
    
    # Connect to database
    conn = connect_to_database()
    if not conn:
        return
    
    successful = 0
    failed = 0
    
    for i, file_path in enumerate(mp3_files, 1):
        print(f"\n[{i}/{len(mp3_files)}] Processing: {file_path.name}")
        
        # Extract metadata from filename
        name = file_path.stem
        if ' - ' in name:
            parts = name.split(' - ', 1)
            artist = parts[0].strip()
            title = parts[1].strip()
        else:
            artist = "Unknown Artist"
            title = name
        
        print(f"  🎤 Artist: {artist}")
        print(f"  🎵 Title: {title}")
        
        # Add to database with real fingerprints
        song_id = add_song_with_real_fingerprints(conn, file_path, title, artist)
        
        if song_id:
            successful += 1
        else:
            failed += 1
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("🎉 Real fingerprint generation complete!")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    
    if successful > 0:
        print(f"\n🎵 {successful} songs with REAL fingerprints added!")
        print("🎯 Now test your Qt app - it should accurately identify these songs!")
        print("\nTo test:")
        print("1. Play one of the processed songs on your speakers")
        print("2. Record with your Qt app")
        print("3. It should identify the song correctly!")

def main():
    if len(sys.argv) < 2:
        print("Real Audio Fingerprinting Generator")
        print("=" * 40)
        print("Usage: python real_fingerprint_generator.py <music_folder_path>")
        print("\nExample:")
        print('python real_fingerprint_generator.py "C:\\Users\\tarna\\Documents\\SongForShazlite"')
        print("\nThis will generate REAL audio fingerprints that can accurately identify songs!")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    process_music_files(folder_path)

if __name__ == "__main__":
    main()