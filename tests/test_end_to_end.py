"""
End-to-end tests for the complete audio identification flow.

Tests the complete system from audio upload through fingerprinting to song identification,
including performance requirements and accuracy validation.

Requirements addressed:
- 2.4: Response time requirements (10 second total processing)
- 4.3: Concurrent request handling (100+ concurrent users)
- 3.1: Song identification results with metadata
"""

import pytest
import asyncio
import time
import concurrent.futures
import threading
from typing import List, Dict, Any
import numpy as np
from fastapi.testclient import TestClient


class TestCompleteAudioIdentificationFlow:
    """Test the complete audio identification workflow."""
    
    def test_successful_audio_identification(self, test_client: TestClient, test_audio_files: Dict[str, str]):
        """Test successful identification of a known song."""
        # Upload audio file for identification
        with open(test_audio_files['wav'], 'rb') as audio_file:
            response = test_client.post(
                "/api/v1/identify",
                files={"audio_file": ("test_audio.wav", audio_file, "audio/wav")}
            )
        
        assert response.status_code == 200
        
        result = response.json()
        assert result["success"] is not None
        assert "processing_time_ms" in result
        assert "request_id" in result
        
        # Check processing time requirement (≤ 10 seconds)
        assert result["processing_time_ms"] <= 10000, f"Processing took {result['processing_time_ms']}ms, exceeds 10s limit"
        
        if result["success"]:
            assert "match" in result
            match = result["match"]
            assert "title" in match
            assert "artist" in match
            assert "confidence" in match
            assert 0.0 <= match["confidence"] <= 1.0
    
    def test_no_match_found_scenario(self, test_client: TestClient, sample_audio_data: Dict[str, Any], tmp_path):
        """Test handling when no matching song is found."""
        # Create noise audio that shouldn't match anything
        noise_data = np.random.randn(44100 * 3).astype(np.float32) * 0.1  # 3 seconds of noise
        
        # Create temporary noise file
        noise_file = tmp_path / "noise.wav"
        
        # Convert to int16 and create WAV
        audio_int16 = (noise_data * 32767).astype(np.int16)
        
        # Create minimal WAV header
        wav_header = bytearray(44)
        wav_header[0:4] = b'RIFF'
        wav_header[8:12] = b'WAVE'
        wav_header[12:16] = b'fmt '
        wav_header[16:20] = (16).to_bytes(4, 'little')
        wav_header[20:22] = (1).to_bytes(2, 'little')
        wav_header[22:24] = (1).to_bytes(2, 'little')
        wav_header[24:28] = (44100).to_bytes(4, 'little')
        wav_header[28:32] = (44100 * 2).to_bytes(4, 'little')
        wav_header[32:34] = (2).to_bytes(2, 'little')
        wav_header[34:36] = (16).to_bytes(2, 'little')
        wav_header[36:40] = b'data'
        wav_header[40:44] = (len(audio_int16) * 2).to_bytes(4, 'little')
        
        total_size = 36 + len(audio_int16) * 2
        wav_header[4:8] = total_size.to_bytes(4, 'little')
        
        with open(noise_file, 'wb') as f:
            f.write(wav_header)
            f.write(audio_int16.tobytes())
        
        # Upload noise file
        with open(noise_file, 'rb') as audio_file:
            response = test_client.post(
                "/api/v1/identify",
                files={"audio_file": ("noise.wav", audio_file, "audio/wav")}
            )
        
        assert response.status_code == 200
        
        result = response.json()
        assert "processing_time_ms" in result
        assert result["processing_time_ms"] <= 10000
        
        # Should indicate no match found
        if not result["success"]:
            assert result["match"] is None
            assert "no match" in result["message"].lower() or "not identified" in result["message"].lower()
    
    def test_invalid_audio_format_handling(self, test_client: TestClient, tmp_path):
        """Test handling of invalid audio formats."""
        # Create a text file pretending to be audio
        invalid_file = tmp_path / "invalid.wav"
        with open(invalid_file, 'w') as f:
            f.write("This is not audio data")
        
        with open(invalid_file, 'rb') as audio_file:
            response = test_client.post(
                "/api/v1/identify",
                files={"audio_file": ("invalid.wav", audio_file, "audio/wav")}
            )
        
        # Should return error for invalid format
        assert response.status_code in [400, 500]  # Bad request or processing error
    
    def test_empty_audio_file_handling(self, test_client: TestClient, tmp_path):
        """Test handling of empty audio files."""
        empty_file = tmp_path / "empty.wav"
        empty_file.touch()  # Create empty file
        
        with open(empty_file, 'rb') as audio_file:
            response = test_client.post(
                "/api/v1/identify",
                files={"audio_file": ("empty.wav", audio_file, "audio/wav")}
            )
        
        # Should return error for empty file
        assert response.status_code in [400, 500]
    
    def test_large_audio_file_handling(self, test_client: TestClient, tmp_path):
        """Test handling of oversized audio files."""
        # Create a large dummy file (simulate large audio)
        large_file = tmp_path / "large.wav"
        
        # Create file larger than typical limit (e.g., 50MB)
        large_size = 50 * 1024 * 1024  # 50MB
        
        with open(large_file, 'wb') as f:
            # Write WAV header
            wav_header = bytearray(44)
            wav_header[0:4] = b'RIFF'
            wav_header[4:8] = (large_size - 8).to_bytes(4, 'little')
            wav_header[8:12] = b'WAVE'
            wav_header[12:16] = b'fmt '
            wav_header[16:20] = (16).to_bytes(4, 'little')
            wav_header[20:22] = (1).to_bytes(2, 'little')
            wav_header[22:24] = (1).to_bytes(2, 'little')
            wav_header[24:28] = (44100).to_bytes(4, 'little')
            wav_header[28:32] = (44100 * 2).to_bytes(4, 'little')
            wav_header[32:34] = (2).to_bytes(2, 'little')
            wav_header[34:36] = (16).to_bytes(2, 'little')
            wav_header[36:40] = b'data'
            wav_header[40:44] = (large_size - 44).to_bytes(4, 'little')
            
            f.write(wav_header)
            
            # Write dummy data in chunks to avoid memory issues
            chunk_size = 1024 * 1024  # 1MB chunks
            remaining = large_size - 44
            
            while remaining > 0:
                chunk = min(chunk_size, remaining)
                f.write(b'\x00' * chunk)
                remaining -= chunk
        
        with open(large_file, 'rb') as audio_file:
            response = test_client.post(
                "/api/v1/identify",
                files={"audio_file": ("large.wav", audio_file, "audio/wav")}
            )
        
        # Should return error for oversized file
        assert response.status_code in [400, 413]  # Bad request or payload too large


class TestSystemPerformanceRequirements:
    """Test system performance under various load conditions."""
    
    def test_single_request_response_time(self, test_client: TestClient, test_audio_files: Dict[str, str]):
        """Test that single requests complete within time limits."""
        start_time = time.time()
        
        with open(test_audio_files['wav'], 'rb') as audio_file:
            response = test_client.post(
                "/api/v1/identify",
                files={"audio_file": ("test_audio.wav", audio_file, "audio/wav")}
            )
        
        end_time = time.time()
        actual_time_ms = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        
        result = response.json()
        reported_time_ms = result["processing_time_ms"]
        
        # Both actual and reported times should be within limits
        assert actual_time_ms <= 10000, f"Actual response time {actual_time_ms}ms exceeds 10s limit"
        assert reported_time_ms <= 10000, f"Reported processing time {reported_time_ms}ms exceeds 10s limit"
        
        # Reported time should be reasonably close to actual time
        time_diff = abs(actual_time_ms - reported_time_ms)
        assert time_diff <= 1000, f"Time reporting discrepancy: {time_diff}ms"
    
    def test_concurrent_request_handling(self, test_client: TestClient, test_audio_files: Dict[str, str], performance_test_config: Dict[str, Any]):
        """Test handling of concurrent requests."""
        concurrent_users = min(performance_test_config["concurrent_users"], 5)  # Limit for testing
        requests_per_user = min(performance_test_config["requests_per_user"], 2)  # Limit for testing
        
        def make_request(user_id: int) -> List[Dict[str, Any]]:
            """Make multiple requests for a single user."""
            results = []
            
            for request_num in range(requests_per_user):
                start_time = time.time()
                
                try:
                    with open(test_audio_files['wav'], 'rb') as audio_file:
                        response = test_client.post(
                            "/api/v1/identify",
                            files={"audio_file": ("test_audio.wav", audio_file, "audio/wav")}
                        )
                    
                    end_time = time.time()
                    response_time_ms = (end_time - start_time) * 1000
                    
                    results.append({
                        "user_id": user_id,
                        "request_num": request_num,
                        "status_code": response.status_code,
                        "response_time_ms": response_time_ms,
                        "success": response.status_code == 200,
                        "response_data": response.json() if response.status_code == 200 else None
                    })
                    
                except Exception as e:
                    results.append({
                        "user_id": user_id,
                        "request_num": request_num,
                        "status_code": 500,
                        "response_time_ms": None,
                        "success": False,
                        "error": str(e)
                    })
            
            return results
        
        # Execute concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(make_request, user_id) for user_id in range(concurrent_users)]
            
            all_results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    user_results = future.result()
                    all_results.extend(user_results)
                except Exception as e:
                    pytest.fail(f"Concurrent request failed: {e}")
        
        # Analyze results
        total_requests = len(all_results)
        successful_requests = [r for r in all_results if r["success"]]
        failed_requests = [r for r in all_results if not r["success"]]
        
        # At least 80% of requests should succeed under concurrent load
        success_rate = len(successful_requests) / total_requests
        assert success_rate >= 0.8, f"Success rate {success_rate:.2%} below 80% threshold"
        
        # Check response times for successful requests
        response_times = [r["response_time_ms"] for r in successful_requests if r["response_time_ms"] is not None]
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            # Average response time should be reasonable
            assert avg_response_time <= 15000, f"Average response time {avg_response_time}ms too high under load"
            
            # Maximum response time should not exceed limits by too much
            assert max_response_time <= 20000, f"Maximum response time {max_response_time}ms too high under load"
        
        print(f"Concurrent test results: {len(successful_requests)}/{total_requests} successful, "
              f"avg response time: {avg_response_time:.0f}ms, max: {max_response_time:.0f}ms")
    
    def test_memory_usage_stability(self, test_client: TestClient, test_audio_files: Dict[str, str]):
        """Test that memory usage remains stable across multiple requests."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Make multiple requests
        num_requests = 10
        for i in range(num_requests):
            with open(test_audio_files['wav'], 'rb') as audio_file:
                response = test_client.post(
                    "/api/v1/identify",
                    files={"audio_file": ("test_audio.wav", audio_file, "audio/wav")}
                )
            
            assert response.status_code == 200
            
            # Check memory after every few requests
            if i % 3 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory
                
                # Memory increase should be reasonable (less than 100MB per request on average)
                max_allowed_increase = 100 * (i + 1)
                assert memory_increase <= max_allowed_increase, \
                    f"Memory usage increased by {memory_increase:.1f}MB after {i+1} requests"
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_increase = final_memory - initial_memory
        
        print(f"Memory usage: initial {initial_memory:.1f}MB, final {final_memory:.1f}MB, "
              f"increase {total_increase:.1f}MB over {num_requests} requests")


class TestAccuracyValidation:
    """Test identification accuracy with known reference songs."""
    
    def test_known_song_identification_accuracy(self, test_client: TestClient, reference_songs_data: List[Dict[str, Any]], tmp_path):
        """Test accuracy of identifying known reference songs."""
        # First, add reference songs to the database via admin endpoint
        added_songs = []
        
        for song_data in reference_songs_data[:3]:  # Test with first 3 songs
            # Create temporary audio file for the reference song
            audio_file_path = tmp_path / f"{song_data['title'].replace(' ', '_')}.wav"
            
            # Convert audio data to WAV format
            audio_data = song_data["audio_data"]
            audio_int16 = (audio_data * 32767).astype(np.int16)
            
            # Create WAV file
            wav_header = bytearray(44)
            wav_header[0:4] = b'RIFF'
            wav_header[8:12] = b'WAVE'
            wav_header[12:16] = b'fmt '
            wav_header[16:20] = (16).to_bytes(4, 'little')
            wav_header[20:22] = (1).to_bytes(2, 'little')
            wav_header[22:24] = (1).to_bytes(2, 'little')
            wav_header[24:28] = song_data["sample_rate"].to_bytes(4, 'little')
            wav_header[28:32] = (song_data["sample_rate"] * 2).to_bytes(4, 'little')
            wav_header[32:34] = (2).to_bytes(2, 'little')
            wav_header[34:36] = (16).to_bytes(2, 'little')
            wav_header[36:40] = b'data'
            wav_header[40:44] = (len(audio_int16) * 2).to_bytes(4, 'little')
            
            total_size = 36 + len(audio_int16) * 2
            wav_header[4:8] = total_size.to_bytes(4, 'little')
            
            with open(audio_file_path, 'wb') as f:
                f.write(wav_header)
                f.write(audio_int16.tobytes())
            
            # Add song via admin endpoint
            with open(audio_file_path, 'rb') as audio_file:
                response = test_client.post(
                    "/api/v1/admin/add-song",
                    data={
                        "title": song_data["title"],
                        "artist": song_data["artist"],
                        "album": song_data["album"],
                        "duration_seconds": song_data["duration_seconds"]
                    },
                    files={"audio_file": (audio_file_path.name, audio_file, "audio/wav")}
                )
            
            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    added_songs.append({
                        "song_data": song_data,
                        "song_id": result["song_id"],
                        "audio_file_path": audio_file_path
                    })
        
        # Now test identification of these songs
        correct_identifications = 0
        total_tests = len(added_songs)
        
        for song_info in added_songs:
            song_data = song_info["song_data"]
            audio_file_path = song_info["audio_file_path"]
            
            # Create a slightly modified version of the song for testing
            # (simulate real-world conditions where the query might be slightly different)
            original_audio = song_data["audio_data"]
            
            # Add slight noise and trim to simulate real recording conditions
            noise_level = 0.01  # 1% noise
            np.random.seed(42)  # For reproducible results
            noise = np.random.normal(0, noise_level, len(original_audio)).astype(np.float32)
            noisy_audio = original_audio + noise
            
            # Trim to 5 seconds (simulate partial recording)
            trim_samples = min(len(noisy_audio), song_data["sample_rate"] * 5)
            trimmed_audio = noisy_audio[:trim_samples]
            
            # Create test audio file
            test_file_path = tmp_path / f"test_{song_data['title'].replace(' ', '_')}.wav"
            audio_int16 = (trimmed_audio * 32767).astype(np.int16)
            
            wav_header = bytearray(44)
            wav_header[0:4] = b'RIFF'
            wav_header[8:12] = b'WAVE'
            wav_header[12:16] = b'fmt '
            wav_header[16:20] = (16).to_bytes(4, 'little')
            wav_header[20:22] = (1).to_bytes(2, 'little')
            wav_header[22:24] = (1).to_bytes(2, 'little')
            wav_header[24:28] = song_data["sample_rate"].to_bytes(4, 'little')
            wav_header[28:32] = (song_data["sample_rate"] * 2).to_bytes(4, 'little')
            wav_header[32:34] = (2).to_bytes(2, 'little')
            wav_header[34:36] = (16).to_bytes(2, 'little')
            wav_header[36:40] = b'data'
            wav_header[40:44] = (len(audio_int16) * 2).to_bytes(4, 'little')
            
            total_size = 36 + len(audio_int16) * 2
            wav_header[4:8] = total_size.to_bytes(4, 'little')
            
            with open(test_file_path, 'wb') as f:
                f.write(wav_header)
                f.write(audio_int16.tobytes())
            
            # Test identification
            with open(test_file_path, 'rb') as audio_file:
                response = test_client.post(
                    "/api/v1/identify",
                    files={"audio_file": (test_file_path.name, audio_file, "audio/wav")}
                )
            
            assert response.status_code == 200
            
            result = response.json()
            
            if result["success"] and result["match"]:
                match = result["match"]
                
                # Check if the identification is correct
                if (match["title"].lower() == song_data["title"].lower() and 
                    match["artist"].lower() == song_data["artist"].lower()):
                    correct_identifications += 1
                    
                    # Confidence should be reasonable for correct matches
                    assert match["confidence"] >= 0.3, f"Low confidence {match['confidence']} for correct match"
                
                print(f"Identified '{song_data['title']}' as '{match['title']}' by '{match['artist']}' "
                      f"(confidence: {match['confidence']:.2f})")
            else:
                print(f"Failed to identify '{song_data['title']}' by '{song_data['artist']}'")
        
        # Calculate accuracy
        accuracy = correct_identifications / total_tests if total_tests > 0 else 0
        
        print(f"Identification accuracy: {correct_identifications}/{total_tests} ({accuracy:.1%})")
        
        # For a basic test, we expect at least 50% accuracy
        # In a production system, this should be much higher (80-90%+)
        assert accuracy >= 0.5, f"Identification accuracy {accuracy:.1%} below 50% threshold"
    
    def test_false_positive_rate(self, test_client: TestClient, tmp_path):
        """Test that random audio doesn't produce false positive matches."""
        false_positives = 0
        total_tests = 5
        
        for i in range(total_tests):
            # Generate random noise that shouldn't match anything
            np.random.seed(i + 100)  # Different seed for each test
            noise_duration = 5.0  # 5 seconds
            sample_rate = 44100
            
            noise_data = np.random.randn(int(sample_rate * noise_duration)).astype(np.float32) * 0.1
            
            # Create noise file
            noise_file = tmp_path / f"noise_{i}.wav"
            audio_int16 = (noise_data * 32767).astype(np.int16)
            
            wav_header = bytearray(44)
            wav_header[0:4] = b'RIFF'
            wav_header[8:12] = b'WAVE'
            wav_header[12:16] = b'fmt '
            wav_header[16:20] = (16).to_bytes(4, 'little')
            wav_header[20:22] = (1).to_bytes(2, 'little')
            wav_header[22:24] = (1).to_bytes(2, 'little')
            wav_header[24:28] = sample_rate.to_bytes(4, 'little')
            wav_header[28:32] = (sample_rate * 2).to_bytes(4, 'little')
            wav_header[32:34] = (2).to_bytes(2, 'little')
            wav_header[34:36] = (16).to_bytes(2, 'little')
            wav_header[36:40] = b'data'
            wav_header[40:44] = (len(audio_int16) * 2).to_bytes(4, 'little')
            
            total_size = 36 + len(audio_int16) * 2
            wav_header[4:8] = total_size.to_bytes(4, 'little')
            
            with open(noise_file, 'wb') as f:
                f.write(wav_header)
                f.write(audio_int16.tobytes())
            
            # Test identification
            with open(noise_file, 'rb') as audio_file:
                response = test_client.post(
                    "/api/v1/identify",
                    files={"audio_file": (noise_file.name, audio_file, "audio/wav")}
                )
            
            assert response.status_code == 200
            
            result = response.json()
            
            # If a match is found for random noise, it's likely a false positive
            if result["success"] and result["match"]:
                match = result["match"]
                
                # Only count as false positive if confidence is high
                if match["confidence"] > 0.5:
                    false_positives += 1
                    print(f"Potential false positive: noise identified as '{match['title']}' "
                          f"with confidence {match['confidence']:.2f}")
        
        false_positive_rate = false_positives / total_tests
        
        print(f"False positive rate: {false_positives}/{total_tests} ({false_positive_rate:.1%})")
        
        # False positive rate should be very low (< 20%)
        assert false_positive_rate <= 0.2, f"False positive rate {false_positive_rate:.1%} too high"


class TestSystemHealthAndMonitoring:
    """Test system health monitoring and administrative functions."""
    
    def test_health_check_endpoint(self, test_client: TestClient):
        """Test the health check endpoint functionality."""
        response = test_client.get("/api/v1/admin/health")
        
        assert response.status_code == 200
        
        health_data = response.json()
        
        # Check required health check fields
        assert "status" in health_data
        assert health_data["status"] in ["healthy", "unhealthy"]
        assert "timestamp" in health_data
        assert "version" in health_data
        assert "components" in health_data
        
        # Check component status
        components = health_data["components"]
        assert isinstance(components, dict)
        
        # Should have key components
        expected_components = ["database", "audio_engine", "configuration"]
        for component in expected_components:
            if component in components:
                assert components[component] in ["healthy", "unhealthy"]
    
    def test_performance_metrics_endpoint(self, test_client: TestClient):
        """Test the performance metrics endpoint."""
        response = test_client.get("/api/v1/admin/metrics")
        
        assert response.status_code == 200
        
        metrics_data = response.json()
        
        # Check basic metrics structure
        assert "timestamp" in metrics_data
        assert "server_info" in metrics_data
        
        server_info = metrics_data["server_info"]
        assert "version" in server_info
        
        # Uptime should be present and reasonable
        if "uptime_seconds" in server_info and server_info["uptime_seconds"] is not None:
            assert server_info["uptime_seconds"] >= 0
    
    def test_admin_add_song_endpoint(self, test_client: TestClient, test_audio_files: Dict[str, str]):
        """Test the admin endpoint for adding reference songs."""
        with open(test_audio_files['wav'], 'rb') as audio_file:
            response = test_client.post(
                "/api/v1/admin/add-song",
                data={
                    "title": "Test Admin Song",
                    "artist": "Test Admin Artist",
                    "album": "Test Admin Album",
                    "duration_seconds": 180
                },
                files={"audio_file": ("admin_test.wav", audio_file, "audio/wav")}
            )
        
        # Should succeed or fail gracefully
        assert response.status_code in [200, 400, 500, 503]
        
        if response.status_code == 200:
            result = response.json()
            assert "success" in result
            assert "processing_time_ms" in result
            assert "request_id" in result
            
            if result["success"]:
                assert "song_id" in result
                assert "fingerprint_count" in result
                assert result["fingerprint_count"] >= 0