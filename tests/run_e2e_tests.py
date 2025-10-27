#!/usr/bin/env python3
"""
End-to-end test runner for the audio fingerprinting system.

This script runs the complete test suite including:
- Complete audio identification flow tests
- System performance and load tests
- Accuracy validation with known reference songs
- Concurrent user simulation

Requirements addressed:
- 2.4: Response time requirements validation
- 4.3: Concurrent request handling validation  
- 3.1: Song identification accuracy validation
"""

import sys
import os
import time
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_dependencies():
    """Check that all required dependencies are available."""
    required_packages = [
        'pytest',
        'fastapi',
        'numpy',
        'psutil'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        print("Install them with: pip install " + " ".join(missing_packages))
        return False
    
    return True


def check_system_components():
    """Check that system components are available."""
    print("Checking system components...")
    
    # Check if audio engine is built
    audio_engine_path = project_root / "audio_engine"
    engine_files = list(audio_engine_path.glob("*.pyd")) + list(audio_engine_path.glob("*.so"))
    
    if not engine_files:
        print("❌ Audio engine not found. Build it first with:")
        print("   cd audio_engine && python setup.py build_ext --inplace")
        return False
    else:
        print(f"✅ Audio engine found: {engine_files[0].name}")
    
    # Check if backend is importable
    try:
        from backend.api.main import create_app
        print("✅ Backend API is importable")
    except ImportError as e:
        print(f"❌ Backend API import failed: {e}")
        return False
    
    # Check if database components are available
    try:
        from backend.database.connection import get_db_session
        print("✅ Database components available")
    except ImportError as e:
        print(f"❌ Database components import failed: {e}")
        return False
    
    return True


def run_test_suite(test_type: str = "all", verbose: bool = False, parallel: bool = False) -> Dict[str, Any]:
    """Run the specified test suite."""
    
    test_results = {
        "start_time": time.time(),
        "test_type": test_type,
        "success": False,
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "skipped_tests": 0,
        "duration_seconds": 0,
        "output": "",
        "errors": []
    }
    
    # Prepare pytest command
    pytest_args = [
        sys.executable, "-m", "pytest",
        str(project_root / "tests"),
        "--tb=short",
        "-v" if verbose else "-q"
    ]
    
    # Add test selection based on type
    if test_type == "basic":
        pytest_args.extend(["-k", "test_successful_audio_identification or test_health_check"])
    elif test_type == "performance":
        pytest_args.extend(["-k", "test_performance or test_concurrent"])
    elif test_type == "accuracy":
        pytest_args.extend(["-k", "test_accuracy or test_known_song"])
    elif test_type == "load":
        pytest_args.extend(["-k", "test_concurrent or test_sustained"])
    # For "all", run everything
    
    # Add parallel execution if requested
    if parallel:
        try:
            import pytest_xdist
            pytest_args.extend(["-n", "auto"])
        except ImportError:
            print("Warning: pytest-xdist not available, running tests sequentially")
    
    # Set environment variables for testing
    env = os.environ.copy()
    env["TESTING"] = "true"
    env["PYTHONPATH"] = str(project_root)
    
    print(f"Running {test_type} tests...")
    print(f"Command: {' '.join(pytest_args)}")
    
    try:
        # Run pytest
        result = subprocess.run(
            pytest_args,
            cwd=project_root,
            env=env,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        test_results["output"] = result.stdout + result.stderr
        test_results["duration_seconds"] = time.time() - test_results["start_time"]
        
        # Parse pytest output for test counts
        output_lines = result.stdout.split('\n')
        for line in output_lines:
            if "passed" in line and "failed" in line:
                # Parse line like "5 passed, 2 failed, 1 skipped in 10.5s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed," and i > 0:
                        test_results["passed_tests"] = int(parts[i-1])
                    elif part == "failed," and i > 0:
                        test_results["failed_tests"] = int(parts[i-1])
                    elif part == "skipped" and i > 0:
                        test_results["skipped_tests"] = int(parts[i-1])
        
        test_results["total_tests"] = (
            test_results["passed_tests"] + 
            test_results["failed_tests"] + 
            test_results["skipped_tests"]
        )
        
        test_results["success"] = result.returncode == 0
        
        if result.returncode != 0:
            test_results["errors"].append(f"pytest exited with code {result.returncode}")
        
    except subprocess.TimeoutExpired:
        test_results["errors"].append("Test execution timed out after 10 minutes")
        test_results["duration_seconds"] = time.time() - test_results["start_time"]
    
    except Exception as e:
        test_results["errors"].append(f"Test execution failed: {str(e)}")
        test_results["duration_seconds"] = time.time() - test_results["start_time"]
    
    return test_results


def print_test_results(results: Dict[str, Any]):
    """Print formatted test results."""
    print("\n" + "="*60)
    print(f"TEST RESULTS - {results['test_type'].upper()}")
    print("="*60)
    
    if results["success"]:
        print("✅ PASSED")
    else:
        print("❌ FAILED")
    
    print(f"Duration: {results['duration_seconds']:.1f} seconds")
    print(f"Total tests: {results['total_tests']}")
    print(f"Passed: {results['passed_tests']}")
    print(f"Failed: {results['failed_tests']}")
    print(f"Skipped: {results['skipped_tests']}")
    
    if results["errors"]:
        print("\nErrors:")
        for error in results["errors"]:
            print(f"  - {error}")
    
    if not results["success"] and results["output"]:
        print("\nTest Output:")
        print("-" * 40)
        # Show last 50 lines of output
        output_lines = results["output"].split('\n')
        for line in output_lines[-50:]:
            print(line)


def run_comprehensive_test_suite(verbose: bool = False) -> bool:
    """Run the complete comprehensive test suite."""
    print("🚀 Starting Comprehensive End-to-End Test Suite")
    print("="*60)
    
    test_suites = [
        ("basic", "Basic functionality tests"),
        ("performance", "Performance and timing tests"),
        ("accuracy", "Accuracy validation tests"),
        ("load", "Load and concurrent user tests")
    ]
    
    all_results = []
    overall_success = True
    
    for test_type, description in test_suites:
        print(f"\n📋 {description}")
        print("-" * 40)
        
        results = run_test_suite(test_type, verbose=verbose)
        all_results.append(results)
        
        if not results["success"]:
            overall_success = False
        
        # Print summary for this suite
        status = "✅ PASSED" if results["success"] else "❌ FAILED"
        print(f"{status} - {results['passed_tests']}/{results['total_tests']} tests passed in {results['duration_seconds']:.1f}s")
    
    # Print comprehensive summary
    print("\n" + "="*60)
    print("COMPREHENSIVE TEST SUITE SUMMARY")
    print("="*60)
    
    total_tests = sum(r["total_tests"] for r in all_results)
    total_passed = sum(r["passed_tests"] for r in all_results)
    total_failed = sum(r["failed_tests"] for r in all_results)
    total_skipped = sum(r["skipped_tests"] for r in all_results)
    total_duration = sum(r["duration_seconds"] for r in all_results)
    
    print(f"Overall Status: {'✅ PASSED' if overall_success else '❌ FAILED'}")
    print(f"Total Duration: {total_duration:.1f} seconds")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Skipped: {total_skipped}")
    
    if overall_success:
        print(f"\n🎉 All test suites passed! Success rate: {total_passed/total_tests:.1%}")
    else:
        print(f"\n⚠️  Some test suites failed. Success rate: {total_passed/total_tests:.1%}")
        
        # Show which suites failed
        failed_suites = [r["test_type"] for r in all_results if not r["success"]]
        print(f"Failed suites: {', '.join(failed_suites)}")
    
    return overall_success


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description="End-to-end test runner for audio fingerprinting system")
    
    parser.add_argument(
        "test_type",
        nargs="?",
        default="all",
        choices=["all", "basic", "performance", "accuracy", "load", "comprehensive"],
        help="Type of tests to run"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "-p", "--parallel",
        action="store_true",
        help="Run tests in parallel (requires pytest-xdist)"
    )
    
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check dependencies and system components"
    )
    
    args = parser.parse_args()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check system components
    if not check_system_components():
        sys.exit(1)
    
    if args.check_only:
        print("✅ All dependencies and system components are available")
        sys.exit(0)
    
    # Run tests
    if args.test_type == "comprehensive":
        success = run_comprehensive_test_suite(verbose=args.verbose)
    else:
        results = run_test_suite(args.test_type, verbose=args.verbose, parallel=args.parallel)
        print_test_results(results)
        success = results["success"]
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()