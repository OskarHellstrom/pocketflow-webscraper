import time
import os
from datetime import datetime

# Set DEBUG_LEVEL from environment or default to 1
DEBUG_LEVEL = int(os.getenv("DEBUG_LEVEL", "1"))

def debug(node_name, message, level=1):
    """
    Simple debug function that prints messages if DEBUG_LEVEL is high enough.
    
    Args:
        node_name: Name of the node being debugged
        message: The debug message
        level: Debug level (1=basic, 2=detailed, 3=verbose)
    """
    if level <= DEBUG_LEVEL:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[DEBUG][{timestamp}][{node_name}] {message}")

def debug_error(node_name, error):
    """
    Debug function specifically for errors, always prints regardless of level.
    
    Args:
        node_name: Name of the node where the error occurred
        error: The error object or message
    """
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[ERROR][{timestamp}][{node_name}] {str(error)}") 