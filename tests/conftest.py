# tests/conftest.py
import sys
from pathlib import Path

# Add the src/ directory to the import path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))