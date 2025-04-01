import pytest
import os
from pathlib import Path
from rlc_cloud_repos.cloud_metadata import get_cloud_metadata, CloudMetadata
from rlc_cloud_repos.repo_config import load_mirror_map, select_mirror, build_repo_config

FIXTURES_DIR = Path(__file__).parent / "fixtures"

@pytest.mark.parametrize("fixture_name,expected_provider,expected_region", [
    ("mock-instance-data.json", "aws", "us-west-2"),
    ("mock-instance-data-azure.json", "azure", "eastus"),
    ("mock-instance-data-bad.json", "unknown", None),
    ("mock-instance-data-gcp.json", "gcp", "us-central1"),
    ("mock-instance-data-oracle.json", "oracle", "us-ashburn-1"),
])
def test_cloud_metadata_and_mirror(monkeypatch, fixture_name, expected_provider, expected_region):
    monkeypatch.setenv("RLC_METADATA_PATH", str(FIXTURES_DIR / fixture_name))
    monkeypatch.setenv("RLC_MIRROR_MAP_PATH", str(FIXTURES_DIR / "mock-mirrors.yaml"))

    metadata = get_cloud_metadata()
    assert isinstance(metadata, CloudMetadata)
    assert metadata.provider == expected_provider
    assert metadata.region == expected_region or metadata.region is not None

    mirror_map = load_mirror_map()
    mirror_url = select_mirror(metadata, mirror_map)
    assert mirror_url.startswith("https://")

    repo_config = build_repo_config(metadata, mirror_url)
    assert repo_config.has_option("base", "baseurl")
    assert "$releasever" in repo_config["base"]["baseurl"]
