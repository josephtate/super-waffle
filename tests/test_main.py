import os
from pathlib import Path

import pytest

from rlc_cloud_repos.main import _configure_repos, main, parse_args

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def mock_get_cloud_metadata(monkeypatch, request):
    if "test_cloud_metadata_suite" not in request.node.nodeid:
        monkeypatch.setattr(
            "rlc_cloud_repos.main.get_cloud_metadata",
            lambda: {
                "provider": "mock",
                "region": "mock-region"
            },
        )


def test_parse_args_default():
    """Test parse_args with default arguments."""
    args = parse_args([])
    assert args.mirror_file is None
    assert not args.force


def test_parse_args_with_values():
    """Test parse_args with specific values."""
    args = parse_args(["--mirror-file", "test.yaml", "--force"])
    assert args.mirror_file == "test.yaml"
    assert args.force


def test_main_with_force_flag(tmp_path, dnf_vars_dir, marker, mirrors_file):
    """Test main function with force flag bypasses marker check."""
    marker.touch()

    result = main(["--force"])
    assert result == 0


def test_main_respects_marker_file(tmp_path, marker):
    """Test main respects existing marker file."""
    marker.touch()

    result = main([])
    assert result == 0


def test_main_creates_marker_file(tmp_path, dnf_vars_dir, marker,
                                  mirrors_file):
    """Test main creates marker file after successful run."""
    result = main([])
    assert result == 0
    assert marker.exists()


def test_main_with_custom_mirror_file(tmp_path, dnf_vars_dir, marker,
                                      mirrors_file):
    """Test main with custom mirror file path."""
    result = main(["--mirror-file", str(mirrors_file)])
    assert result == 0


def test_main_handles_configuration_error(tmp_path, monkeypatch):
    """Test main handles configuration errors gracefully."""
    monkeypatch.setattr(
        "rlc_cloud_repos.main._configure_repos",
        lambda x: (_ for _ in ()).throw(Exception("Test error")),
    )
    result = main(["--force"])
    assert result == 1


def test_configure_repos_writes_touchfile(tmp_path, dnf_vars_dir, marker,
                                          mirrors_file):
    """Test _configure_repos writes marker file."""
    _configure_repos(str(mirrors_file))
    assert marker.exists()
    assert "Configured on" in marker.read_text()


def test_configure_repos_invalid_mirror_file():
    """Test _configure_repos with invalid mirror file."""
    with pytest.raises(Exception):
        _configure_repos("nonexistent.yaml")
