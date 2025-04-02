# tests/test_cloud_metadata_suite.py
"""
Test Suite: Cloud Metadata Detection & Mirror Selection

This module validates:
- Cloud provider & region extraction from cloud-init metadata
- Mirror URL selection based on provider/region
- YUM repo config generation
"""

import pytest
import os
from pathlib import Path
from rlc_cloud_repos.cloud_metadata import get_cloud_metadata, CloudMetadata, _query_cloud_init_fallback
from rlc_cloud_repos.repo_config import load_mirror_map, select_mirror, build_repo_config

# Directory containing test fixtures (mock metadata and mirror maps)
FIXTURES_DIR = Path(__file__).parent / "fixtures"

@pytest.mark.parametrize("fixture_name,expected_provider,expected_region", [
    ("mock-instance-data.json", "aws", "us-west-2"),
    ("mock-instance-data-azure.json", "azure", "eastus"),
    ("mock-instance-data-bad.json", "unknown", "fallback-region"),
    ("mock-instance-data-gcp.json", "gcp", "us-central1"),
    ("mock-instance-data-oracle.json", "oracle", "us-ashburn-1"),
])
def test_cloud_metadata_and_mirror(monkeypatch, fixture_name, expected_provider, expected_region):
    monkeypatch.setenv("RLC_METADATA_PATH", str(FIXTURES_DIR / fixture_name))
    monkeypatch.setenv("RLC_MIRROR_MAP_PATH", str(FIXTURES_DIR / "mock-mirrors.yaml"))

    # ✅ Only patch the fallback logic for the broken metadata case
    if "bad" in fixture_name:
        monkeypatch.setattr("rlc_cloud_repos.cloud_metadata._query_cloud_init_fallback", lambda: {
            "provider": "unknown",
            "region": "fallback-region",
            "instance_id": "fallback-id"
        })

    metadata = get_cloud_metadata()
    assert isinstance(metadata, CloudMetadata)
    assert metadata.provider == expected_provider
    assert metadata.region == expected_region

    mirror_map = load_mirror_map()
    mirror_url = select_mirror(metadata, mirror_map)
    assert mirror_url.startswith("https://")

    repo_config = build_repo_config(metadata, mirror_url)
    assert repo_config.has_option("base", "baseurl")
    assert "$releasever" in repo_config["base"]["baseurl"]
