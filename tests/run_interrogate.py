"""
Interrogate CLI Wrapper.

This script runs the 'interrogate' tool on the core codebase and redirects the 
full verbose output to 'interrogate_output.txt'.

Usage:
    uv run python tests/run_interrogate.py
    
    # Or to run the CLI directly if installed:
    uv run interrogate -vv core
"""

import subprocess
import os

def run_interrogate():
    # Target directory relative to project root
    target_dir = os.path.join(os.path.dirname(__file__), "..", "core")
    output_file = "interrogate_output.txt"
    
    print(f"Running interrogate on {os.path.abspath(target_dir)}...")
    
    # Run via uv to ensure environment is correct
    cmd = ["uv", "run", "interrogate", "-vv", target_dir]
    
    try:
        with open(output_file, "w") as f:
            subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, check=True)
        print(f"Success. Full report written to {output_file}")
    except subprocess.CalledProcessError:
        print(f"Interrogate reported issues (or failed). Check {output_file} for details.")
    except Exception as e:
        print(f"Error running interrogate: {e}")

if __name__ == "__main__":
    run_interrogate()
