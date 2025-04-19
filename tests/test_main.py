
# tests/test_main.py
"""Tests for the main module."""

import os
from unittest.mock import patch

import pytest

from rlc_cloud_repos.main import main, parse_args
from rlc_cloud_repos.repo_config import DEFAULT_MIRROR_PATH


def test_parse_args_default():
    """Test parse_args with default arguments."""
    args = parse_args([])
    assert args.mirror_file is None
    assert args.force is False


def test_parse_args_with_values():
    """Test parse_args with specific values."""
    args = parse_args(["--mirror-file", "test.yaml", "--force"])
    assert args.mirror_file == "test.yaml"
    assert args.force is True


@patch("rlc_cloud_repos.main.setup_logging")
@patch("rlc_cloud_repos.main.check_touchfile")
@patch("rlc_cloud_repos.main._configure_repos")
def test_main_success(mock_configure, mock_check, mock_logging):
    """Test main function success path."""
    result = main(["--force"])  # Force flag to skip touchfile check
    assert result == 0
    mock_configure.assert_called_once_with(DEFAULT_MIRROR_PATH)
    mock_check.assert_not_called()  # Should be skipped due to force flag


@patch("rlc_cloud_repos.main.setup_logging")
@patch("rlc_cloud_repos.main.check_touchfile")
@patch("rlc_cloud_repos.main._configure_repos")
def test_main_with_mirror_file(mock_configure, mock_check, mock_logging):
    """Test main function with custom mirror file."""
    custom_path = "custom/path.yaml"
    result = main(["--mirror-file", custom_path, "--force"])
    assert result == 0
    mock_configure.assert_called_once_with(custom_path)


@patch("rlc_cloud_repos.main.setup_logging")
@patch("rlc_cloud_repos.main._configure_repos", side_effect=Exception("Test error"))
def test_main_error_handling(mock_configure, mock_logging):
    """Test main function error handling."""
    result = main(["--force"])
    assert result == 1
    mock_configure.assert_called_once()
