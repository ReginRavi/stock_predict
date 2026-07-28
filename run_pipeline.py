#!/usr/bin/env python3
"""
Wrapper script to run Scripts/run_pipeline.py from the root directory.
"""
import sys
import os
import subprocess
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

if __name__ == "__main__":
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    scripts_pipeline = Path(__file__).parent / "Scripts" / "run_pipeline.py"
    cmd = [sys.executable, str(scripts_pipeline)] + sys.argv[1:]
    sys.exit(subprocess.call(cmd, env=env))

