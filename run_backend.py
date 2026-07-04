#!/usr/bin/env python3
"""Run Lecturify AI backend. Execute from lecturify_ai/ directory."""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

os.chdir(ROOT)

from backend.app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
