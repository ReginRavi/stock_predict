#!/usr/bin/env python3
"""
Wrapper script to run Scripts/run_pipeline.py from the root directory.
"""
import sys
import subprocess
from pathlib import Path

if __name__ == "__main__":
    scripts_pipeline = Path(__file__).parent / "Scripts" / "run_pipeline.py"
    cmd = [sys.executable, str(scripts_pipeline)] + sys.argv[1:]
    sys.exit(subprocess.call(cmd))
