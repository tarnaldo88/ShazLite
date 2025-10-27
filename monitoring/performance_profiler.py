#!/usr/bin/env python3
"""
Performance profiler for the Audio Fingerprinting System.

This module provides tools to profile and analyze performance bottlenecks
in audio processing, database queries, and API endpoints.

Requirements addressed:
- 2.2: Audio processing performance optimization
- 2.4: Total processing time optimization  
- 4.2: Database query optimization
- 4.5: System performance monitoring
"""

import time
import psutil
import threading
import statistics
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager
import json
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class PerformanceMetric:
    """Container for performance measurement data."""
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    memory_start_mb: Optional[float] = None
    memory_end_mb: Optional[float] = None
    memory_peak_mb: Optional[float] = None
    cpu_percent: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def finish(self, end_time: Optional[float] = None):
        """Mark the metric as finished and calculate duration."""
        self.end_time = end_time or time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000


class PerformanceProfiler:
    """Main performance profiler class."""
    
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.active_metrics: Dict[str, PerformanceMetric] = {}
        self.process = psutil.Process()
        self._monitoring = False
        self._monitor_thread = None
        
    def start_monitoring(self, interval: float = 0.1):
        """Start continuous system monitoring."""
        if self._monitoring:
            return
            
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_system, args=(interval,))
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop continuous system monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
    
    def _monitor_system(self, interval: float):
        """Background system monitoring thread."""
        while self._monitoring:
            try:
                # Update memory usage for active metrics
                current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
                
                for metric in self.active_metrics.values():
                    if metric.memory_peak_mb is None or current_memory > metric.memory_peak_mb:
                        metric.memory_peak_mb = current_memory
                
                time.sleep(interval)
            except Exception:
                # Ignore monitoring errors
                pass
    
    @contextmanager
    def profile(self, name: str, **metadata):
        """Context manager for profiling code blocks."""
        metric = self.start_metric(name, **metadata)
        try:
            yield metric
        finally:
            self.end_metric(name)
    
    def start_metric(self, name: str, **metadata) -> PerformanceMetric:
        """Start measuring a performance metric."""
        current_time = time.time()
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        metric = PerformanceMetric(
            name=name,
            start_time=current_time,
            memory_start_mb=current_memory,
            memory_peak_mb=current_memory,
            metadata=metadata
        )
        
        self.active_metrics[name] = metric
        return metric
    
    def end_metric(self, name: str) -> Optional[PerformanceMetric]:
        """End measuring a performance metric."""
        if name not in self.active_metrics:
            return None
            
        metric = self.active_metrics.pop(name)
        current_time = time.time()
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        metric.finish(current_time)
        metric.memory_end_mb = current_memory
        
        # Calculate CPU usage (approximate)
        try:
            metric.cpu_percent = self.process.cpu_percent()
        except Exception:
            metric.cpu_percent = None
        
        self.metrics.append(metric)
        return metric
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary statistics for all metrics."""
        if not self.metrics:
            return {}
        
        # Group metrics by name
        grouped_metrics = {}
        for metric in self.metrics:
            if metric.name not in grouped_metrics:
                grouped_metrics[metric.name] = []
            grouped_metrics[metric.name].append(metric)
        
        summary = {}
        for name, metrics_list in grouped_metrics.items():
            durations = [m.duration_ms for m in metrics_list if m.duration_ms is not None]
            memory_usage = [m.memory_end_mb - m.memory_start_mb for m in metrics_list 
                          if m.memory_start_mb is not None and m.memory_end_mb is not None]
            
            if durations:
                summary[name] = {
                    'count': len(durations),
                    'duration_ms': {
                        'min': min(durations),
                        'max': max(durations),
                        'mean': statistics.mean(durations),
                        'median': statistics.median(durations),
                        'std_dev': statistics.stdev(durations) if len(durations) > 1 else 0
                    }
                }
                
                if memory_usage:
                    summary[name]['memory_delta_mb'] = {
                        'min': min(memory_usage),
                        'max': max(memory_usage),
                        'mean': statistics.mean(memory_usage)
                    }
        
        return summary
    
    def export_metrics(self, filename: str):
        """Export metrics to JSON file."""
        data = {
            'metrics': [
                {
                    'name': m.name,
                    'start_time': m.start_time,
                    'end_time': m.end_time,
                    'duration_ms': m.duration_ms,
                    'memory_start_mb': m.memory_start_mb,
                    'memory_end_mb': m.memory_end_mb,
                    'memory_peak_mb': m.memory_peak_mb,
                    'cpu_percent': m.cpu_percent,
                    'metadata': m.metadata
                }
                for m in self.metrics
            ],
            'summary': self.get_metrics_summary()
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)


class AudioProcessingProfiler:
    """Specialized profiler for audio processing operations."""
    
    def __init__(self, profiler: PerformanceProfiler):
        self.profiler = profiler
    
    def profile_fingerprint_generation(self, audio_data, sample_rate: int, channels: int):
        """Profile audio fingerprint generation."""
        metadata = {
            'audio_length_samples': len(audio_data),
            'sample_rate': sample_rate,
            'channels': channels,
            'duration_seconds': len(audio_data) / sample_rate
        }
        
        with self.profiler.profile('fingerprint_generation', **metadata) as metric:
            try:
                # Import here to avoid circular imports
                from audio_engine.fingerprint_api import AudioFingerprintEngine
                
                engine = AudioFingerprintEngine()
                
                # Profile preprocessing
                with self.profiler.profile('audio_preprocessing'):
                    preprocessed_data, new_rate, new_channels = engine.preprocess_audio(
                        audio_data, sample_rate, channels
                    )
                
                # Profile fingerprint computation
                with self.profiler.profile('fingerprint_computation'):
                    result = engine.generate_fingerprint(preprocessed_data, new_rate, new_channels)
                
                # Add result metadata
                metric.metadata.update({
                    'fingerprint_count': result.count,
                    'fingerprints_per_second': result.count / metadata['duration_seconds'] if metadata['duration_seconds'] > 0 else 0
                })
                
                return result
                
            except Exception as e:
                metric.metadata['error'] = str(e)
                raise
    
    def profile_batch_processing(self, audio_samples: List[Dict], song_ids: List[str]):
        """Profile batch audio processing."""
        metadata = {
            'batch_size': len(audio_samples),
            'total_audio_duration': sum(
                len(sample['data']) / sample['sample_rate'] 
                for sample in audio_samples
            )
        }
        
        with self.profiler.profile('batch_processing', **metadata) as metric:
            try:
                from audio_engine.fingerprint_api import AudioFingerprintEngine
                
                engine = AudioFingerprintEngine()
                results = engine.batch_process_reference_songs(audio_samples, song_ids)
                
                # Add result metadata
                successful_results = [r for r in results if r.success]
                total_fingerprints = sum(r.fingerprint_count for r in successful_results)
                
                metric.metadata.update({
                    'successful_songs': len(successful_results),
                    'failed_songs': len(results) - len(successful_results),
                    'total_fingerprints': total_fingerprints,
                    'avg_fingerprints_per_song': total_fingerprints / len(successful_results) if successful_results else 0
                })
                
                return results
                
            except Exception as e:
                metric.metadata['error'] = str(e)
                raise


class DatabaseProfiler:
    """Specialized profiler for database operations."""
    
    def __init__(self, profiler: PerformanceProfiler):
        self.profiler = profiler
    
    def profile_fingerprint_search(self, fingerprints: List, min_matches: int = 5):
        """Profile fingerprint database search."""
        metadata = {
            'fingerprint_count': len(fingerprints),
            'min_matches': min_matches
        }
        
        with self.profiler.profile('fingerprint_search', **metadata) as metric:
            try:
                from backend.database.connection import get_db_session
                from backend.database.repositories import MatchRepository
                
                with get_db_session() as session:
                    match_repo = MatchRepository(session)
                    
                    # Profile the search operation
                    result = match_repo.find_best_match(fingerprints, min_matches)
                    
                    # Add result metadata
                    metric.metadata.update({
                        'match_found': result is not None,
                        'confidence': result.confidence if result else 0,
                        'match_count': result.match_count if result else 0
                    })
                    
                    return result
                    
            except Exception as e:
                metric.metadata['error'] = str(e)
                raise
    
    def profile_song_insertion(self, title: str, artist: str, fingerprints: List):
        """Profile song and fingerprint insertion."""
        metadata = {
            'fingerprint_count': len(fingerprints),
            'title': title,
            'artist': artist
        }
        
        with self.profiler.profile('song_insertion', **metadata) as metric:
            try:
                from backend.database.population_utils import DatabasePopulator
                
                populator = DatabasePopulator()
                song_id = populator.add_song_with_fingerprints(
                    title=title,
                    artist=artist,
                    fingerprints=fingerprints,
                    skip_duplicates=True
                )
                
                metric.metadata.update({
                    'song_id': song_id,
                    'success': song_id is not None
                })
                
                return song_id
                
            except Exception as e:
                metric.metadata['error'] = str(e)
                raise


class APIEndpointProfiler:
    """Specialized profiler for API endpoint performance."""
    
    def __init__(self, profiler: PerformanceProfiler):
        self.profiler = profiler
    
    def profile_identification_request(self, audio_file_path: str):
        """Profile complete audio identification request."""
        metadata = {
            'audio_file': audio_file_path,
            'file_size_mb': os.path.getsize(audio_file_path) / 1024 / 1024
        }
        
        with self.profiler.profile('identification_request', **metadata) as metric:
            try:
                import requests
                
                # Profile file upload and processing
                with open(audio_file_path, 'rb') as f:
                    files = {'audio_file': f}
                    
                    start_time = time.time()
                    response = requests.post(
                        'http://localhost:8000/api/v1/identify',
                        files=files,
                        timeout=30
                    )
                    end_time = time.time()
                
                # Add response metadata
                metric.metadata.update({
                    'status_code': response.status_code,
                    'response_time_ms': (end_time - start_time) * 1000,
                    'success': response.status_code == 200
                })
                
                if response.status_code == 200:
                    result = response.json()
                    metric.metadata.update({
                        'server_processing_time_ms': result.get('processing_time_ms'),
                        'match_found': result.get('success', False),
                        'confidence': result.get('match', {}).get('confidence') if result.get('match') else None
                    })
                
                return response
                
            except Exception as e:
                metric.metadata['error'] = str(e)
                raise


def create_performance_report(profiler: PerformanceProfiler, output_file: str = None):
    """Create a comprehensive performance report."""
    summary = profiler.get_metrics_summary()
    
    report = {
        'timestamp': time.time(),
        'total_metrics': len(profiler.metrics),
        'summary': summary,
        'recommendations': []
    }
    
    # Analyze performance and generate recommendations
    for name, stats in summary.items():
        duration_stats = stats.get('duration_ms', {})
        mean_duration = duration_stats.get('mean', 0)
        
        # Check against performance requirements
        if 'fingerprint' in name.lower():
            if mean_duration > 5000:  # 5 second requirement
                report['recommendations'].append({
                    'type': 'performance_warning',
                    'metric': name,
                    'issue': f'Average duration {mean_duration:.0f}ms exceeds 5s fingerprint requirement',
                    'suggestion': 'Optimize audio processing algorithm or increase CPU resources'
                })
        
        elif 'identification' in name.lower():
            if mean_duration > 10000:  # 10 second requirement
                report['recommendations'].append({
                    'type': 'performance_warning',
                    'metric': name,
                    'issue': f'Average duration {mean_duration:.0f}ms exceeds 10s total processing requirement',
                    'suggestion': 'Optimize database queries and audio processing pipeline'
                })
        
        elif 'database' in name.lower() or 'search' in name.lower():
            if mean_duration > 3000:  # 3 second database requirement
                report['recommendations'].append({
                    'type': 'performance_warning',
                    'metric': name,
                    'issue': f'Average duration {mean_duration:.0f}ms exceeds 3s database requirement',
                    'suggestion': 'Optimize database indexes and query performance'
                })
        
        # Check memory usage
        memory_stats = stats.get('memory_delta_mb', {})
        if memory_stats:
            mean_memory = memory_stats.get('mean', 0)
            if mean_memory > 100:  # 100MB threshold
                report['recommendations'].append({
                    'type': 'memory_warning',
                    'metric': name,
                    'issue': f'Average memory usage {mean_memory:.1f}MB is high',
                    'suggestion': 'Investigate memory leaks and optimize data structures'
                })
    
    # Output report
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
    
    return report


def main():
    """Main function for running performance profiling."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Audio Fingerprinting Performance Profiler')
    parser.add_argument('--mode', choices=['audio', 'database', 'api', 'full'], 
                       default='full', help='Profiling mode')
    parser.add_argument('--output', help='Output file for results')
    parser.add_argument('--audio-file', help='Audio file for testing')
    parser.add_argument('--iterations', type=int, default=5, help='Number of test iterations')
    
    args = parser.parse_args()
    
    # Create profiler
    profiler = PerformanceProfiler()
    profiler.start_monitoring()
    
    try:
        if args.mode in ['audio', 'full']:
            print("Profiling audio processing...")
            audio_profiler = AudioProcessingProfiler(profiler)
            
            # Generate test audio if no file provided
            if not args.audio_file:
                import numpy as np
                sample_rate = 44100
                duration = 5.0
                frequency = 440.0
                t = np.linspace(0, duration, int(sample_rate * duration), False)
                audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)
            else:
                # Load audio file (simplified)
                audio_data = np.random.randn(44100 * 5).astype(np.float32)  # Placeholder
            
            for i in range(args.iterations):
                print(f"  Iteration {i+1}/{args.iterations}")
                audio_profiler.profile_fingerprint_generation(audio_data, 44100, 1)
        
        if args.mode in ['database', 'full']:
            print("Profiling database operations...")
            db_profiler = DatabaseProfiler(profiler)
            
            # Create dummy fingerprints for testing
            from backend.models.audio import Fingerprint
            test_fingerprints = [
                Fingerprint(hash_value=i, time_offset_ms=i*100, frequency_1=440.0, frequency_2=880.0)
                for i in range(100)
            ]
            
            for i in range(args.iterations):
                print(f"  Iteration {i+1}/{args.iterations}")
                try:
                    db_profiler.profile_fingerprint_search(test_fingerprints)
                except Exception as e:
                    print(f"    Database test failed: {e}")
        
        if args.mode in ['api', 'full'] and args.audio_file:
            print("Profiling API endpoints...")
            api_profiler = APIEndpointProfiler(profiler)
            
            for i in range(args.iterations):
                print(f"  Iteration {i+1}/{args.iterations}")
                try:
                    api_profiler.profile_identification_request(args.audio_file)
                except Exception as e:
                    print(f"    API test failed: {e}")
        
        # Generate report
        print("\nGenerating performance report...")
        output_file = args.output or f"performance_report_{int(time.time())}.json"
        report = create_performance_report(profiler, output_file)
        
        print(f"Performance report saved to: {output_file}")
        
        # Print summary
        print("\nPerformance Summary:")
        for name, stats in report['summary'].items():
            duration_stats = stats.get('duration_ms', {})
            print(f"  {name}:")
            print(f"    Count: {stats['count']}")
            print(f"    Avg Duration: {duration_stats.get('mean', 0):.1f}ms")
            print(f"    Max Duration: {duration_stats.get('max', 0):.1f}ms")
        
        # Print recommendations
        if report['recommendations']:
            print("\nRecommendations:")
            for rec in report['recommendations']:
                print(f"  {rec['type'].upper()}: {rec['issue']}")
                print(f"    Suggestion: {rec['suggestion']}")
    
    finally:
        profiler.stop_monitoring()


if __name__ == "__main__":
    main()