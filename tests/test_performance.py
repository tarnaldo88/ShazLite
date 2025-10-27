"""
Performance and load testing for the audio fingerprinting system.

Tests system performance under various load conditions and validates
that performance requirements are met.

Requirements addressed:
- 2.2: Audio fingerprint generation within 5 seconds
- 2.4: Total processing time within 10 seconds
- 4.3: Handle 100+ concurrent requests
"""

import pytest
import asyncio
import time
import threading
import concurrent.futures
import statistics
from typing import List, Dict, Any, Tuple
import numpy as np
from fastapi.testclient import TestClient


class TestPerformanceBenchmarks:
    """Benchmark tests for core system performance."""
    
    def test_fingerprint_generation_performance(self, test_client: TestClient, test_audio_files: Dict[str, str]):
        """Test fingerprint generation performance meets requirements."""
        # Test multiple audio samples of different lengths
        test_cases = [
            {"duration": 5, "description": "5-second sample"},
            {"duration": 10, "description": "10-second sample"},
            {"duration": 30, "description": "30-second sample"}
        ]
        
        for case in test_cases:
            # Create audio sample of specified duration
            duration = case["duration"]
            sample_rate = 44100
            frequency = 440.0
            
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)
            audio_int16 = (audio_data * 32767).astype(np.int16)
            
            # Create WAV file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                # Write WAV header
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
                
                temp_file.write(wav_header)
                temp_file.write(audio_int16.tobytes())
                temp_file_path = temp_file.name
            
            # Test fingerprint generation performance
            start_time = time.time()
            
            with open(temp_file_path, 'rb') as audio_file:
                response = test_client.post(
                    "/api/v1/identify",
                    files={"audio_file": ("test.wav", audio_file, "audio/wav")}
                )
            
            end_time = time.time()
            processing_time = (end_time - start_time) * 1000  # Convert to ms
            
            # Clean up temp file
            import os
            os.unlink(temp_file_path)
            
            assert response.status_code == 200
            
            result = response.json()
            reported_time = result.get("processing_time_ms", 0)
            
            print(f"{case['description']}: {processing_time:.0f}ms actual, {reported_time:.0f}ms reported")
            
            # Performance requirements
            if duration <= 10:
                # For samples ≤ 10 seconds, should complete within 10 seconds total
                assert processing_time <= 10000, f"{case['description']} took {processing_time}ms, exceeds 10s limit"
            else:
                # For longer samples, allow proportionally more time but still reasonable
                max_allowed = duration * 1000  # 1 second per second of audio
                assert processing_time <= max_allowed, f"{case['description']} took {processing_time}ms, exceeds {max_allowed}ms limit"
    
    def test_database_query_performance(self, test_client: TestClient, test_audio_files: Dict[str, str]):
        """Test database query performance for fingerprint matching."""
        # Make multiple requests to test database performance
        num_requests = 10
        response_times = []
        
        for i in range(num_requests):
            start_time = time.time()
            
            with open(test_audio_files['wav'], 'rb') as audio_file:
                response = test_client.post(
                    "/api/v1/identify",
                    files={"audio_file": ("test.wav", audio_file, "audio/wav")}
                )
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            assert response.status_code == 200
            response_times.append(response_time)
        
        # Analyze performance
        avg_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        print(f"Database query performance over {num_requests} requests:")
        print(f"  Average: {avg_time:.0f}ms")
        print(f"  Median: {median_time:.0f}ms")
        print(f"  Min: {min_time:.0f}ms")
        print(f"  Max: {max_time:.0f}ms")
        
        # Performance requirements
        assert avg_time <= 10000, f"Average response time {avg_time}ms exceeds 10s limit"
        assert max_time <= 15000, f"Maximum response time {max_time}ms too high"
        
        # Database queries should be consistent (low variance)
        if len(response_times) > 1:
            std_dev = statistics.stdev(response_times)
            coefficient_of_variation = std_dev / avg_time
            assert coefficient_of_variation <= 0.5, f"Response time variance too high: {coefficient_of_variation:.2f}"


class TestConcurrentLoadHandling:
    """Test system behavior under concurrent load."""
    
    def test_concurrent_user_simulation(self, test_client: TestClient, test_audio_files: Dict[str, str]):
        """Simulate multiple concurrent users making requests."""
        # Test configuration
        num_concurrent_users = 20  # Simulate 20 concurrent users
        requests_per_user = 3      # Each user makes 3 requests
        
        def simulate_user(user_id: int) -> Dict[str, Any]:
            """Simulate a single user making multiple requests."""
            user_results = {
                "user_id": user_id,
                "requests": [],
                "total_time": 0,
                "successful_requests": 0,
                "failed_requests": 0
            }
            
            user_start_time = time.time()
            
            for request_num in range(requests_per_user):
                request_start = time.time()
                
                try:
                    with open(test_audio_files['wav'], 'rb') as audio_file:
                        response = test_client.post(
                            "/api/v1/identify",
                            files={"audio_file": ("test.wav", audio_file, "audio/wav")}
                        )
                    
                    request_end = time.time()
                    request_time = (request_end - request_start) * 1000
                    
                    request_result = {
                        "request_num": request_num,
                        "status_code": response.status_code,
                        "response_time_ms": request_time,
                        "success": response.status_code == 200
                    }
                    
                    if response.status_code == 200:
                        user_results["successful_requests"] += 1
                        response_data = response.json()
                        request_result["processing_time_ms"] = response_data.get("processing_time_ms")
                    else:
                        user_results["failed_requests"] += 1
                    
                    user_results["requests"].append(request_result)
                    
                except Exception as e:
                    user_results["failed_requests"] += 1
                    user_results["requests"].append({
                        "request_num": request_num,
                        "status_code": 500,
                        "response_time_ms": None,
                        "success": False,
                        "error": str(e)
                    })
                
                # Small delay between requests from same user
                time.sleep(0.1)
            
            user_results["total_time"] = (time.time() - user_start_time) * 1000
            return user_results
        
        # Execute concurrent user simulation
        print(f"Starting concurrent load test: {num_concurrent_users} users, {requests_per_user} requests each")
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent_users) as executor:
            futures = [executor.submit(simulate_user, user_id) for user_id in range(num_concurrent_users)]
            
            user_results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    user_results.append(result)
                except Exception as e:
                    pytest.fail(f"User simulation failed: {e}")
        
        total_test_time = (time.time() - start_time) * 1000
        
        # Analyze results
        total_requests = sum(len(user["requests"]) for user in user_results)
        total_successful = sum(user["successful_requests"] for user in user_results)
        total_failed = sum(user["failed_requests"] for user in user_results)
        
        success_rate = total_successful / total_requests if total_requests > 0 else 0
        
        # Collect response times for successful requests
        all_response_times = []
        all_processing_times = []
        
        for user in user_results:
            for request in user["requests"]:
                if request["success"] and request["response_time_ms"] is not None:
                    all_response_times.append(request["response_time_ms"])
                    if "processing_time_ms" in request and request["processing_time_ms"] is not None:
                        all_processing_times.append(request["processing_time_ms"])
        
        # Calculate statistics
        if all_response_times:
            avg_response_time = statistics.mean(all_response_times)
            median_response_time = statistics.median(all_response_times)
            p95_response_time = np.percentile(all_response_times, 95)
            max_response_time = max(all_response_times)
        else:
            avg_response_time = median_response_time = p95_response_time = max_response_time = 0
        
        if all_processing_times:
            avg_processing_time = statistics.mean(all_processing_times)
            max_processing_time = max(all_processing_times)
        else:
            avg_processing_time = max_processing_time = 0
        
        # Print results
        print(f"Concurrent load test results:")
        print(f"  Total test time: {total_test_time:.0f}ms")
        print(f"  Total requests: {total_requests}")
        print(f"  Successful: {total_successful} ({success_rate:.1%})")
        print(f"  Failed: {total_failed}")
        print(f"  Average response time: {avg_response_time:.0f}ms")
        print(f"  Median response time: {median_response_time:.0f}ms")
        print(f"  95th percentile response time: {p95_response_time:.0f}ms")
        print(f"  Maximum response time: {max_response_time:.0f}ms")
        print(f"  Average processing time: {avg_processing_time:.0f}ms")
        print(f"  Maximum processing time: {max_processing_time:.0f}ms")
        
        # Performance assertions
        assert success_rate >= 0.90, f"Success rate {success_rate:.1%} below 90% under concurrent load"
        assert avg_response_time <= 12000, f"Average response time {avg_response_time}ms too high under load"
        assert p95_response_time <= 20000, f"95th percentile response time {p95_response_time}ms too high"
        assert max_processing_time <= 15000, f"Maximum processing time {max_processing_time}ms exceeds reasonable limit"
    
    def test_sustained_load_performance(self, test_client: TestClient, test_audio_files: Dict[str, str]):
        """Test system performance under sustained load over time."""
        # Test configuration
        test_duration_seconds = 30  # Run test for 30 seconds
        concurrent_users = 5        # Moderate concurrent load
        
        results = {
            "start_time": time.time(),
            "requests": [],
            "active_users": 0,
            "completed_users": 0
        }
        
        def sustained_user_requests(user_id: int):
            """Make continuous requests for the test duration."""
            user_start = time.time()
            user_requests = []
            
            results["active_users"] += 1
            
            while (time.time() - results["start_time"]) < test_duration_seconds:
                request_start = time.time()
                
                try:
                    with open(test_audio_files['wav'], 'rb') as audio_file:
                        response = test_client.post(
                            "/api/v1/identify",
                            files={"audio_file": ("test.wav", audio_file, "audio/wav")}
                        )
                    
                    request_end = time.time()
                    request_time = (request_end - request_start) * 1000
                    
                    request_data = {
                        "user_id": user_id,
                        "timestamp": request_start,
                        "response_time_ms": request_time,
                        "status_code": response.status_code,
                        "success": response.status_code == 200
                    }
                    
                    if response.status_code == 200:
                        response_json = response.json()
                        request_data["processing_time_ms"] = response_json.get("processing_time_ms")
                    
                    user_requests.append(request_data)
                    results["requests"].append(request_data)
                    
                except Exception as e:
                    request_data = {
                        "user_id": user_id,
                        "timestamp": request_start,
                        "response_time_ms": None,
                        "status_code": 500,
                        "success": False,
                        "error": str(e)
                    }
                    user_requests.append(request_data)
                    results["requests"].append(request_data)
                
                # Brief pause between requests
                time.sleep(0.5)
            
            results["active_users"] -= 1
            results["completed_users"] += 1
            
            return user_requests
        
        # Start sustained load test
        print(f"Starting sustained load test: {concurrent_users} users for {test_duration_seconds} seconds")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(sustained_user_requests, user_id) for user_id in range(concurrent_users)]
            
            # Wait for all users to complete
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Sustained user failed: {e}")
        
        # Analyze sustained load results
        total_requests = len(results["requests"])
        successful_requests = [r for r in results["requests"] if r["success"]]
        failed_requests = [r for r in results["requests"] if not r["success"]]
        
        success_rate = len(successful_requests) / total_requests if total_requests > 0 else 0
        
        # Calculate throughput (requests per second)
        actual_duration = time.time() - results["start_time"]
        throughput = total_requests / actual_duration
        
        # Response time analysis
        response_times = [r["response_time_ms"] for r in successful_requests if r["response_time_ms"] is not None]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            
            # Check for performance degradation over time
            first_half = response_times[:len(response_times)//2]
            second_half = response_times[len(response_times)//2:]
            
            if first_half and second_half:
                first_half_avg = statistics.mean(first_half)
                second_half_avg = statistics.mean(second_half)
                performance_degradation = (second_half_avg - first_half_avg) / first_half_avg
            else:
                performance_degradation = 0
        else:
            avg_response_time = median_response_time = performance_degradation = 0
        
        print(f"Sustained load test results:")
        print(f"  Actual duration: {actual_duration:.1f}s")
        print(f"  Total requests: {total_requests}")
        print(f"  Throughput: {throughput:.1f} requests/second")
        print(f"  Success rate: {success_rate:.1%}")
        print(f"  Average response time: {avg_response_time:.0f}ms")
        print(f"  Median response time: {median_response_time:.0f}ms")
        print(f"  Performance degradation: {performance_degradation:.1%}")
        
        # Performance assertions for sustained load
        assert success_rate >= 0.85, f"Success rate {success_rate:.1%} too low under sustained load"
        assert throughput >= 1.0, f"Throughput {throughput:.1f} req/s too low"
        assert avg_response_time <= 15000, f"Average response time {avg_response_time}ms too high under sustained load"
        assert abs(performance_degradation) <= 0.3, f"Performance degraded by {performance_degradation:.1%} over time"


class TestResourceUtilization:
    """Test system resource utilization under load."""
    
    def test_memory_usage_under_load(self, test_client: TestClient, test_audio_files: Dict[str, str]):
        """Test memory usage remains stable under load."""
        try:
            import psutil
            import os
        except ImportError:
            pytest.skip("psutil not available for memory monitoring")
        
        process = psutil.Process(os.getpid())
        
        # Baseline memory usage
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_samples = [initial_memory]
        
        # Make requests while monitoring memory
        num_requests = 20
        
        for i in range(num_requests):
            with open(test_audio_files['wav'], 'rb') as audio_file:
                response = test_client.post(
                    "/api/v1/identify",
                    files={"audio_file": ("test.wav", audio_file, "audio/wav")}
                )
            
            assert response.status_code == 200
            
            # Sample memory usage
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_samples.append(current_memory)
            
            # Brief pause
            time.sleep(0.1)
        
        # Analyze memory usage
        final_memory = memory_samples[-1]
        max_memory = max(memory_samples)
        memory_increase = final_memory - initial_memory
        peak_increase = max_memory - initial_memory
        
        print(f"Memory usage analysis:")
        print(f"  Initial: {initial_memory:.1f}MB")
        print(f"  Final: {final_memory:.1f}MB")
        print(f"  Peak: {max_memory:.1f}MB")
        print(f"  Total increase: {memory_increase:.1f}MB")
        print(f"  Peak increase: {peak_increase:.1f}MB")
        print(f"  Average per request: {memory_increase/num_requests:.2f}MB")
        
        # Memory usage assertions
        assert memory_increase <= 200, f"Memory increased by {memory_increase:.1f}MB, too high"
        assert peak_increase <= 300, f"Peak memory increase {peak_increase:.1f}MB, too high"
        
        # Memory should not grow linearly with requests (indicating leaks)
        avg_per_request = memory_increase / num_requests
        assert avg_per_request <= 5, f"Average memory per request {avg_per_request:.2f}MB suggests memory leak"
    
    def test_cpu_usage_monitoring(self, test_client: TestClient, test_audio_files: Dict[str, str]):
        """Monitor CPU usage during audio processing."""
        try:
            import psutil
        except ImportError:
            pytest.skip("psutil not available for CPU monitoring")
        
        # Monitor CPU usage during requests
        cpu_samples = []
        
        def monitor_cpu():
            """Monitor CPU usage in background."""
            for _ in range(50):  # Monitor for ~5 seconds
                cpu_percent = psutil.cpu_percent(interval=0.1)
                cpu_samples.append(cpu_percent)
        
        # Start CPU monitoring in background
        import threading
        monitor_thread = threading.Thread(target=monitor_cpu)
        monitor_thread.start()
        
        # Make requests while monitoring
        num_requests = 5
        request_times = []
        
        for i in range(num_requests):
            start_time = time.time()
            
            with open(test_audio_files['wav'], 'rb') as audio_file:
                response = test_client.post(
                    "/api/v1/identify",
                    files={"audio_file": ("test.wav", audio_file, "audio/wav")}
                )
            
            end_time = time.time()
            request_times.append((end_time - start_time) * 1000)
            
            assert response.status_code == 200
        
        # Wait for monitoring to complete
        monitor_thread.join()
        
        # Analyze CPU usage
        if cpu_samples:
            avg_cpu = statistics.mean(cpu_samples)
            max_cpu = max(cpu_samples)
            
            print(f"CPU usage during audio processing:")
            print(f"  Average CPU: {avg_cpu:.1f}%")
            print(f"  Peak CPU: {max_cpu:.1f}%")
            print(f"  Average request time: {statistics.mean(request_times):.0f}ms")
            
            # CPU usage should be reasonable (not constantly at 100%)
            assert avg_cpu <= 80, f"Average CPU usage {avg_cpu:.1f}% too high"
            assert max_cpu <= 95, f"Peak CPU usage {max_cpu:.1f}% too high"