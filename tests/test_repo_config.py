from pathlib import Path

import pytest

from rlc.cloud_repos.repo_config import load_mirror_map, select_mirror


def test_load_mirror_map_success(mirrors_file):
    """Test successful loading of mirror map."""
    mirror_map = load_mirror_map(str(mirrors_file))
    assert isinstance(mirror_map, dict)
    assert "azure" in mirror_map
    assert "default" in mirror_map


def test_load_mirror_map_file_not_found():
    """Test load_mirror_map with nonexistent file."""
    with pytest.raises(FileNotFoundError):
        load_mirror_map("nonexistent.yaml")


def test_load_mirror_map_invalid_yaml(tmp_path):
    """Test load_mirror_map with invalid YAML."""
    invalid_yaml = tmp_path / "invalid.yaml"
    invalid_yaml.write_text("{ invalid: yaml: content")
    with pytest.raises(ValueError):
        load_mirror_map(str(invalid_yaml))


@pytest.mark.parametrize(
    "provider,region",
    [
        ("azure", "eastus"),
        ("azure", "westus2"),
        ("azure", "nonexistent-region"),
        ("gcp", "us-central1"),
        ("oracle", "us-ashburn-1"),
        ("unknown-provider", "unknown-region"),
    ],
)
def test_select_mirror_returns_non_empty_urls(mirrors_file, provider, region):
    """Test select_mirror always returns two non-empty URLs."""
    mirror_map = load_mirror_map(str(mirrors_file))

    primary, backup = select_mirror(
        {"provider": provider, "region": region}, mirror_map
    )

    assert isinstance(primary, str)
    assert isinstance(backup, str)
    assert primary != ""
    assert primary.startswith("https://")


def test_select_mirror_provider_fallback(mirrors_file):
    """Test select_mirror falls back to provider default."""
    mirror_map = load_mirror_map(str(mirrors_file))

    primary, backup = select_mirror(
        {"provider": "azure", "region": "unknown"}, mirror_map
    )
    assert primary == "https://depot.eastus.prod.azure.ciq.com"


def test_select_mirror_global_fallback(mirrors_file):
    """Test select_mirror falls back to global default."""
    mirror_map = load_mirror_map(str(mirrors_file))

    primary, backup = select_mirror(
        {"provider": "unknown", "region": "unknown"}, mirror_map
    )
    assert primary == "https://depot.eastus.prod.azure.ciq.com"


def test_select_mirror_no_fallback():
    """Test select_mirror raises error when no fallback exists."""
    mirror_map = {"azure": {"eastus": {"primary": "url"}}}  # No default entry

    with pytest.raises(ValueError):
        select_mirror({"provider": "unknown", "region": "unknown"}, mirror_map)
