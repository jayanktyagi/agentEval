"""
tests/conftest.py

Adds backend/ to sys.path so tests can import from app.*
without needing to cd into backend/ first.

This runs automatically before any test file.
"""

import sys
import os

# Walk up from tests/ to project root, then into backend/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))