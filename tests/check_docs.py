"""
Docstring Coverage Checker.

This utility uses the 'interrogate' package to check docstring coverage across 
the core logic of the application. It provides a more detailed breakdown than 
the default interrogate CLI by listing specific missing docstrings and their 
line numbers.

Usage:
    uv run python tests/check_docs.py
    
    # Or if interrogate is installed in your environment:
    python tests/check_docs.py
"""

import os
import sys
from interrogate import coverage

def run_coverage_check():
    # Target directory relative to project root
    target_dir = os.path.join(os.path.dirname(__file__), "..", "core")
    abs_target = os.path.abspath(target_dir)
    
    if not os.path.exists(abs_target):
        print(f"Error: Target directory not found: {abs_target}")
        sys.exit(1)

    print(f"Checking docstrings in: {abs_target}")
    
    # Initialize coverage check
    cov = coverage.InterrogateCoverage(paths=[abs_target])
    results = cov.get_coverage()

    print(f"Total Project Coverage: {results.perc_covered:.2f}%")
    print("-" * 40)

    # Detailed breakdown per file
    for file_result in results.file_results:
        # Use relative paths for cleaner output
        rel_path = os.path.relpath(file_result.filename, os.getcwd())
        print(f"{rel_path}: {file_result.perc_covered:.1f}% ({file_result.covered}/{file_result.total})")
        
        if file_result.perc_covered < 100:
            print("  Missing Docstrings:")
            for node in file_result.nodes:
                if not node.covered:
                    # 'node.name' identifies the function, class, or method
                    print(f"    - {node.name} (line {node.lineno})")
            print()

if __name__ == "__main__":
    run_coverage_check()
