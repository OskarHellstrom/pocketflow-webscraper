#!/usr/bin/env python3
"""
Run the web research agent with debug logging to a file.
"""

import os
import sys
import time
import subprocess
from datetime import datetime

def main():
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Generate timestamp for log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"logs/debug_{timestamp}.log"
    
    # Ask user for debug level
    debug_level = input("Enter debug level (1=basic, 2=detailed, 3=verbose) [default=1]: ").strip()
    if not debug_level or not debug_level.isdigit() or int(debug_level) < 1 or int(debug_level) > 3:
        debug_level = "1"
    
    print(f"Running agent with debug level {debug_level}...")
    print(f"Debug log will be saved to: {log_file}")
    
    # Start the agent process with output redirection
    try:
        with open(log_file, 'w') as f:
            # Set environment variables
            env = os.environ.copy()
            env['DEBUG_LEVEL'] = debug_level
            
            # Start the process
            process = subprocess.Popen(
                ["python", "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                env=env
            )
            
            # Process and write output to both console and file
            for line in process.stdout:
                sys.stdout.write(line)
                f.write(line)
                f.flush()
            
            # Wait for process to complete
            process.wait()
            
            # Report completion
            print(f"\nAgent has completed. Debug log saved to {log_file}")
            
            # Ask if user wants to analyze the log file
            analyze = input("Do you want to analyze the debug log for errors? (y/n) [default=y]: ").strip().lower()
            if analyze == "" or analyze.startswith("y"):
                print("\nAnalyzing debug log...")
                subprocess.run(["python", "check_debug.py", log_file])
                
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
    except Exception as e:
        print(f"\nError running agent: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 