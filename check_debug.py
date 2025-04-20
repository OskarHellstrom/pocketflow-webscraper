#!/usr/bin/env python3
"""
Debug log analyzer for the web research agent.
This script processes a debug log file and extracts error information.
"""

import sys
import re
import argparse
from datetime import datetime

def parse_log(log_file):
    """Parse a log file and extract debug and error messages."""
    debug_pattern = r'\[DEBUG\]\[([^\]]+)\]\[([^\]]+)\] (.+)'
    error_pattern = r'\[ERROR\]\[([^\]]+)\]\[([^\]]+)\] (.+)'
    
    debug_entries = []
    error_entries = []
    
    with open(log_file, 'r') as f:
        for line in f:
            # Check for ERROR entries
            error_match = re.search(error_pattern, line)
            if error_match:
                timestamp, node, message = error_match.groups()
                error_entries.append({
                    'timestamp': timestamp,
                    'node': node,
                    'message': message
                })
                continue
            
            # Check for DEBUG entries
            debug_match = re.search(debug_pattern, line)
            if debug_match:
                timestamp, node, message = debug_match.groups()
                debug_entries.append({
                    'timestamp': timestamp,
                    'node': node,
                    'message': message
                })
    
    return debug_entries, error_entries

def analyze_errors(debug_entries, error_entries):
    """Analyze errors and find related debug entries."""
    results = []
    
    for error in error_entries:
        # Find debug entries around the error (within 5 seconds)
        error_time = datetime.strptime(error['timestamp'], '%H:%M:%S')
        context = []
        
        for debug in debug_entries:
            debug_time = datetime.strptime(debug['timestamp'], '%H:%M:%S')
            time_diff = abs((error_time - debug_time).total_seconds())
            
            # Include debug entries within 5 seconds before the error
            if time_diff <= 5 and debug_time <= error_time:
                context.append(debug)
        
        results.append({
            'error': error,
            'context': context
        })
    
    return results

def display_results(results):
    """Display analysis results."""
    if not results:
        print("No errors found in the log.")
        return
    
    print(f"Found {len(results)} errors in the log:\n")
    
    for i, result in enumerate(results):
        error = result['error']
        context = result['context']
        
        print(f"ERROR {i+1}: [{error['timestamp']}] {error['node']}")
        print(f"Message: {error['message']}")
        
        if context:
            print("\nContext (debug entries before the error):")
            for j, debug in enumerate(reversed(context[-5:])):  # Show last 5 entries in reverse order
                print(f"  {j+1}. [{debug['timestamp']}] {debug['node']}: {debug['message']}")
        
        print("-" * 80)

def main():
    parser = argparse.ArgumentParser(description="Analyze debug logs from the web research agent.")
    parser.add_argument('log_file', help="Path to the log file")
    args = parser.parse_args()
    
    try:
        debug_entries, error_entries = parse_log(args.log_file)
        results = analyze_errors(debug_entries, error_entries)
        display_results(results)
    except Exception as e:
        print(f"Error analyzing log file: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 