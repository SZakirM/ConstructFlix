#!/usr/bin/env python
"""Test runner script"""
import sys
import os
import unittest

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Change to project directory  
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Discover and run tests
loader = unittest.TestLoader()
suite = loader.discover('app/tests')
runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)

# Exit with appropriate code
sys.exit(0 if result.wasSuccessful() else 1)

