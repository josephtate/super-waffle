# tests/conftest.py
import sys
from pathlib import Path
import pytest
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_get_cloud_metadata(request):
    if "test_cloud_metadata_suite" not in request.node.nodeid:
        with patch("rlc_cloud_repos.cloud_metadata.get_cloud_metadata", return_value={"provider": "mock", "region": "mock-region"}):
            yield

# Add the src/ directory to the import path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
