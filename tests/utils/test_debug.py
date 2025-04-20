import unittest
import io
import sys
import os
from unittest.mock import patch
from datetime import datetime

# Add the project root to the path so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from utils.debug import debug, debug_error

class TestDebug(unittest.TestCase):
    
    def setUp(self):
        # Capture stdout for testing
        self.held_output = io.StringIO()
        sys.stdout = self.held_output
    
    def tearDown(self):
        # Reset stdout
        sys.stdout = sys.__stdout__
    
    @patch('utils.debug.DEBUG_LEVEL', 2)
    def test_debug_message_printed_when_level_is_sufficient(self):
        """Test that debug messages are printed when level is sufficient"""
        debug("TestNode", "Test message", level=1)
        output = self.held_output.getvalue()
        
        # Check that output contains expected components
        self.assertIn("[DEBUG]", output)
        self.assertIn("[TestNode]", output)
        self.assertIn("Test message", output)
    
    @patch('utils.debug.DEBUG_LEVEL', 1)
    def test_debug_message_not_printed_when_level_is_insufficient(self):
        """Test that debug messages are not printed when level is insufficient"""
        debug("TestNode", "Test message", level=2)
        output = self.held_output.getvalue()
        
        # Output should be empty
        self.assertEqual("", output)
    
    def test_debug_error_always_prints(self):
        """Test that debug_error always prints regardless of debug level"""
        debug_error("TestNode", "Test error")
        output = self.held_output.getvalue()
        
        # Check that output contains expected components
        self.assertIn("[ERROR]", output)
        self.assertIn("[TestNode]", output)
        self.assertIn("Test error", output)

if __name__ == '__main__':
    unittest.main() 