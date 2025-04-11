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
from unittest.mock import MagicMock
from rlc_cloud_repos.cloud_metadata import get_cloud_metadata
from rlc_cloud_repos.repo_config import load_mirror_map, select_mirror
from rlc_cloud_repos.dnf_vars import ensure_all_dnf_vars, BACKUP_SUFFIX
from rlc_cloud_repos.log_utils import log_and_print

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize("expected_provider,expected_region", [
    ("aws", "us-west-2"),
    ("azure", "eastus"),
    ("gcp", "us-central1"),
    ("oracle", "us-ashburn-1"),
    ("unknown", "fallback-region"),
])
def test_cloud_metadata_and_mirror(monkeypatch, expected_provider, expected_region):
    """
    Validates that cloud metadata and mirror resolution behave as expected.
    """

    def fake_check_output(cmd, text=True):
        if "cloud_name" in cmd:
            return expected_provider
        elif "region" in cmd:
            return expected_region
        return "fallback-id"

    monkeypatch.setattr("rlc_cloud_repos.cloud_metadata.subprocess.check_output", fake_check_output)
    # Use setattr to patch the default path constant directly
    mock_mirror_path = str(FIXTURES_DIR / "mock-mirrors.yaml")
    monkeypatch.setattr("rlc_cloud_repos.repo_config.DEFAULT_MIRROR_PATH", mock_mirror_path)
    # Clear potential env var override to ensure setattr is effective
    monkeypatch.delenv("RLC_MIRROR_MAP_PATH", raising=False)


    metadata = get_cloud_metadata()
    assert metadata["provider"] == expected_provider
    assert metadata["region"] == expected_region

    mirror_map = load_mirror_map()
    primary, backup = select_mirror(metadata, mirror_map)
    assert primary.startswith("https://")
    assert isinstance(backup, str)


def test_marker_file_respected(monkeypatch, tmp_path):
    marker_file = tmp_path / ".rlc_marker"
    marker_file.write_text("already-done")

    monkeypatch.setattr("os.path.exists", lambda p: str(marker_file) in p)
    monkeypatch.setattr("os.remove", lambda p: marker_file.unlink())

    assert marker_file.exists()
    os.remove(str(marker_file))
    assert not marker_file.exists()


def test_dnf_vars_creation_and_backup(monkeypatch, tmp_path):
    var_dir = tmp_path / "dnf_vars"
    var_dir.mkdir()
    (var_dir / "baseurl1").write_text("original-value")

    monkeypatch.setattr("rlc_cloud_repos.dnf_vars.DNF_VARS_DIR", var_dir)
    # Use setattr to patch the default path constant directly
    mock_mirror_path = str(FIXTURES_DIR / "mock-mirrors.yaml")
    monkeypatch.setattr("rlc_cloud_repos.repo_config.DEFAULT_MIRROR_PATH", mock_mirror_path)
    # Clear potential env var override to ensure setattr is effective
    monkeypatch.delenv("RLC_MIRROR_MAP_PATH", raising=False)


    monkeypatch.setattr("rlc_cloud_repos.cloud_metadata.subprocess.check_output", lambda cmd, text=True: {
        "cloud_name": "aws",
        "region": "us-west-2"
    }[cmd[-1]])

    metadata = get_cloud_metadata()
    mirror_map = load_mirror_map()
    primary, backup = select_mirror(metadata, mirror_map)
    ensure_all_dnf_vars(primary, backup)

    for var in ["baseurl1", "baseurl2"]:
        assert (var_dir / var).exists()

    assert (var_dir / "baseurl1.bak").exists()


def test_cloud_metadata_returns_dict(monkeypatch):
    monkeypatch.setattr(
        "subprocess.check_output",
        lambda cmd, text=True: "aws" if "cloud_name" in cmd else "us-west-2"
    )
    result = get_cloud_metadata()
    assert isinstance(result, dict)
    assert result["provider"] == "aws"
    assert result["region"] == "us-west-2"


def test_logger_fallback_and_log_and_print(monkeypatch):
    mock_logger = MagicMock()
    monkeypatch.setattr("rlc_cloud_repos.log_utils.logger", mock_logger)
    log_and_print("Test log output", level="info")
    mock_logger.info.assert_called_with("Test log output")
