#!/usr/bin/env python3
"""
CSV Data Processing Application - Entry Point.

Processes all CSV files from input/ and saves results to output/.
Designed for GitHub Actions CI/CD on push and pull_request.
"""

import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.processor import run

if __name__ == "__main__":
    sys.exit(run())
