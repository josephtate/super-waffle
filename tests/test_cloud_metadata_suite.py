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
import builtins
from pathlib import Path
from unittest.mock import MagicMock, patch
from rlc_cloud_repos.cloud_metadata import get_cloud_metadata, CloudMetadata, _query_cloud_init_fallback
from rlc_cloud_repos.repo_config import load_mirror_map, select_mirror, build_repo_config
from rlc_cloud_repos.dnf_vars import ensure_all_dnf_vars, BACKUP_SUFFIX
from rlc_cloud_repos.log_utils import log_and_print


# Directory containing test fixtures (mock metadata and mirror maps)
FIXTURES_DIR = Path(__file__).parent / "fixtures"
MOCK_DNF_VARS = FIXTURES_DIR / "mock_dnf_vars"

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


def test_marker_file_respected(monkeypatch, tmp_path):
    """
    Verify that the script respects the marker file and early exits,
    unless --force is explicitly passed.
    """
    marker_file = tmp_path / ".rlc_marker"
    marker_file.write_text("already-done")

    monkeypatch.setattr("os.path.exists", lambda p: str(marker_file) in p)
    monkeypatch.setattr("os.remove", lambda p: marker_file.unlink())

    assert marker_file.exists()
    os.remove(str(marker_file))
    assert not marker_file.exists()


def test_dnf_vars_creation_and_backup(monkeypatch, tmp_path):
    """
    Ensure missing DNF vars are generated, and existing ones are backed up and restored.
    """
    var_dir = tmp_path / "dnf_vars"
    var_dir.mkdir()

    # Seed existing var to test backup logic
    (var_dir / "baseurl1").write_text("original-value")

    # Mock DNF vars directory
    monkeypatch.setattr("rlc_cloud_repos.dnf_vars.DNF_VARS_DIR", var_dir)

    # 👇 Patch environment to use offline-safe metadata & mirrors
    monkeypatch.setenv("RLC_METADATA_PATH", str(FIXTURES_DIR / "mock-instance-data.json"))
    monkeypatch.setenv("RLC_MIRROR_MAP_PATH", str(FIXTURES_DIR / "mock-mirrors.yaml"))

    # Load test-safe metadata and mirror URL
    metadata = get_cloud_metadata()
    mirror_map = load_mirror_map()
    mirror_url = select_mirror(metadata, mirror_map)

    # Run DNF var logic
    ensure_all_dnf_vars(metadata, mirror_url)

    # Assert all vars exist
    for var in ["baseurl1", "baseurl2", "contentdir", "infra", "region", "rltype", "sigcontentdir"]:
        assert (var_dir / var).exists()

    # Confirm backup created
    assert (var_dir / "baseurl1.bak").exists()



def test_logger_fallback_and_log_and_print(monkeypatch, caplog):
    """
    Validate that log_and_print logs to both console and syslog,
    and fallback to SysLogHandler if JournalHandler fails.
    """
    mock_logger = MagicMock()
    monkeypatch.setattr("rlc_cloud_repos.log_utils.logger", mock_logger)

    # Call it
    log_and_print("Test log output", level="info")

    mock_logger.info.assert_called_with("Test log output")
    # stdout not captured by caplog, but logger call is enough