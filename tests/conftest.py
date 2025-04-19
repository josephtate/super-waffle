# tests/conftest.py
import sys
from pathlib import Path
import pytest


@pytest.fixture
def dnf_vars_dir(tmp_path, monkeypatch):
    """Fixture to mock DNF_VARS_DIR to use a temp directory."""
    dnf_path = tmp_path / "dnf" / "vars"
    dnf_path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("rlc_cloud_repos.dnf_vars.DNF_VARS_DIR", dnf_path)
    return dnf_path


# Add the src/ directory to the import path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
