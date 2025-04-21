# tests/test_cloud_metadata_suite.py
"""
Test Suite: Cloud Metadata Detection & Mirror Selection

This module validates:
- Cloud provider & region extraction from cloud-init metadata
- Mirror URL selection based on provider/region
- YUM repo config generation
"""

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from rlc_cloud_repos.cloud_metadata import get_cloud_metadata
from rlc_cloud_repos.dnf_vars import ensure_all_dnf_vars
from rlc_cloud_repos.log_utils import log_and_print
from rlc_cloud_repos.repo_config import load_mirror_map, select_mirror

MIRROR_FIXTURES = (
    Path(__file__).parent.parent / "src/rlc_cloud_repos/data/ciq-mirrors.yaml"
)


@pytest.mark.parametrize(
    "expected_provider,expected_region",
    [
        ("aws", "us-west-2"),
        ("azure", "eastus"),
        ("gcp", "us-central1"),
        ("oracle", "us-ashburn-1"),
        ("unknown", "fallback-region"),
    ],
)
def test_cloud_metadata_and_mirror(
    monkeypatch, mirrors_file, expected_provider, expected_region
):
    """
    Validates that cloud metadata and mirror resolution behave as expected.
    """

    def fake_check_output(cmd, text=True):
        if "cloud_name" in cmd:
            return expected_provider
        elif "region" in cmd:
            return expected_region

    monkeypatch.setattr(
        "rlc_cloud_repos.cloud_metadata.subprocess.check_output", fake_check_output
    )
    # Use setattr to patch the default path constant directly
    mock_mirror_path = str(mirrors_file)
    # Clear potential env var override to ensure setattr is effective
    metadata = get_cloud_metadata()
    assert metadata["provider"] == expected_provider
    assert metadata["region"] == expected_region

    mirror_map = load_mirror_map(mock_mirror_path)
    primary, backup = select_mirror(metadata, mirror_map)
    assert primary.startswith("https://")
    assert isinstance(backup, str)


def test_dnf_vars_creation_and_backup(monkeypatch, mirrors_file, tmp_path):
    var_dir = tmp_path / "dnf_vars"
    var_dir.mkdir()
    (var_dir / "baseurl1").write_text("original-value")

    # Use setattr to patch the default path constant directly
    mock_mirror_path = str(mirrors_file)

    monkeypatch.setattr(
        "rlc_cloud_repos.cloud_metadata.subprocess.check_output",
        lambda cmd, text=True: {"cloud_name": "aws", "region": "us-west-2"}[cmd[-1]],
    )

    metadata = get_cloud_metadata()
    mirror_map = load_mirror_map(mock_mirror_path)
    primary, backup = select_mirror(metadata, mirror_map)
    ensure_all_dnf_vars(var_dir, primary, backup)

    for var in ["baseurl1", "baseurl2"]:
        assert (var_dir / var).exists()

    assert (var_dir / "baseurl1.bak").exists()


def test_cloud_metadata_returns_dict(monkeypatch):
    monkeypatch.setattr(
        "subprocess.check_output",
        lambda cmd, text=True: "aws" if "cloud_name" in cmd else "us-west-2",
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
    log_and_print("Test log output", level="info")
    mock_logger.info.assert_called_with("Test log output")


def test_metadata_file_for_missing_values(mirrors_file):
    mirror_map = load_mirror_map(str(mirrors_file))

    # The mirror map must provide a default provider section with primary and backup values
    assert "default" in mirror_map, "No default section found in the mirror map"
    assert "primary" in mirror_map["default"], "No primary URL found in default section"
    assert "backup" in mirror_map["default"], "No backup URL found in default section"
    mirror_map.pop("default")

    for key, value in mirror_map.items():
        # Each provider must provide a default with primary and backup values
        assert "default" in value, f"No default section found in provider '{key}'"
        assert (
            "primary" in value["default"]
        ), f"No primary URL found in default section of provider '{key}'"
        assert (
            "backup" in value["default"]
        ), f"No backup URL found in default section of provider '{key}'"
        value.pop("default")
        for region, r_map in value.items():
            assert (
                "primary" in r_map
            ), f"No primary URL found in region '{region}' of provider '{key}'"
            assert (
                "backup" in r_map
            ), f"No backup URL found in region '{region}' of provider '{key}'"
