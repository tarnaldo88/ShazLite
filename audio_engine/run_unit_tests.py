#!/usr/bin/env python3
"""
Simple test runner for audio engine unit tests.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == "__main__":
    try:
        from test_unit import create_test_suite
        import unittest
        
        print("Running Audio Engine Unit Tests...")
        print("-" * 40)
        
        # Create and run test suite
        suite = create_test_suite()
        runner = unittest.TextTestRunner(verbosity=1)
        result = runner.run(suite)
        
        # Print summary
        print("\n" + "-" * 40)
        if result.wasSuccessful():
            print(f"✓ All {result.testsRun} tests passed!")
            sys.exit(0)
        else:
            print(f"✗ {len(result.failures + result.errors)} test(s) failed out of {result.testsRun}")
            sys.exit(1)
            
    except ImportError as e:
        print(f"Failed to import test modules: {e}")
        print("Make sure the audio engine is built: python setup.py build_ext --inplace")
        sys.exit(1)