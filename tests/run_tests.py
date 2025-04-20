#!/usr/bin/env python3
import unittest
import sys
import os

def run_tests():
    """Discover and run all tests in the tests directory"""
    # Add the project root to the path so imports work correctly
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.insert(0, project_root)
    
    # Find and run all tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)  # tests directory
    suite = loader.discover(start_dir=start_dir, pattern='test_*.py')
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return appropriate exit code
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests()) 