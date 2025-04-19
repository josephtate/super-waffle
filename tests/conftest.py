# tests/conftest.py
import sys
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def mock_get_cloud_metadata(monkeypatch, request):
    if "test_cloud_metadata_suite" not in request.node.nodeid:
        monkeypatch.setattr(
            "rlc_cloud_repos.cloud_metadata.get_cloud_metadata",
            lambda: {"provider": "mock", "region": "mock-region"},
        )


# Add the src/ directory to the import path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
