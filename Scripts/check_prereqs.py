"""
Prerequisite verifier for the K8s Observability AI Agent.

Checks:
- Python version (>=3.10)
- Required packages from requirements.txt
- Optional environment variables presence
"""

from __future__ import annotations

import os
import sys
from importlib import metadata
from typing import List, Tuple


MIN_PYTHON = (3, 10)
REQUIRED_PACKAGES = [
    "fastapi",
    "uvicorn",
    "httpx",
    "pydantic",
    "pydantic-settings",
    "kubernetes",
    "python-dotenv",
]
OPTIONAL_ENV_VARS = [
    "PROMETHEUS_BASE_URL",
    "LOKI_BASE_URL",
    "ALERTMANAGER_URL",
    "GEMINI_MODEL",
    "GEMINI_API_KEY",
    "KUBE_CONTEXT",
    "REQUEST_TIMEOUT_SECONDS",
    "LOG_LEVEL",
]


def check_python() -> Tuple[bool, str]:
    if sys.version_info >= MIN_PYTHON:
        return True, f"Python {sys.version_info.major}.{sys.version_info.minor} detected"
    return False, f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer required"


def check_packages() -> Tuple[bool, List[str]]:
    missing: List[str] = []
    for package in REQUIRED_PACKAGES:
        try:
            metadata.version(package)
        except metadata.PackageNotFoundError:
            missing.append(package)
    return len(missing) == 0, missing


def check_env_vars() -> List[str]:
    missing: List[str] = []
    for key in OPTIONAL_ENV_VARS:
        if not os.getenv(key):
            missing.append(key)
    return missing


def main() -> int:
    ok_python, python_msg = check_python()
    print(f"[{'OK' if ok_python else 'FAIL'}] {python_msg}")

    ok_packages, missing_packages = check_packages()
    if ok_packages:
        print("[OK] Required packages installed")
    else:
        print("[FAIL] Missing packages: " + ", ".join(sorted(missing_packages)))

    missing_env = check_env_vars()
    if missing_env:
        print("[WARN] Optional env vars not set: " + ", ".join(sorted(missing_env)))
    else:
        print("[OK] Optional env vars present")

    if not ok_python or not ok_packages:
        print("\nAction: install missing prerequisites, e.g. `pip install -r requirements.txt`.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
