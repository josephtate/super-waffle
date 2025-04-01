import configparser
import os
import yaml
from pathlib import Path
from typing import Any, Optional
from rlc_cloud_repos.cloud_metadata import CloudMetadata


def load_mirror_map(yaml_path: str = None) -> dict[str, Any]:
    """
    Load mirror mapping from a YAML file.
    Path can be overridden via env var or passed directly.
    """
    yaml_path = (
        yaml_path or
        os.getenv("RLC_MIRROR_MAP_PATH") or
        "/etc/rlc-cloud-repos/mirrors.yaml"
    )
    path = Path(yaml_path)

    if not path.exists():
        raise FileNotFoundError(f"Mirror config YAML not found at {yaml_path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in mirror map: {e}")


def select_mirror(metadata: CloudMetadata, mirror_map: dict[str, Any]) -> str:
    """
    Select the appropriate mirror URL using primary/backup logic.
    """
    provider = metadata.provider.lower()
    region = metadata.region

    provider_map = mirror_map.get(provider, {})

    if isinstance(provider_map, dict):
        region_map = provider_map.get(region)
        if isinstance(region_map, dict):
            return region_map.get("primary") or region_map.get("backup")

        if "default" in provider_map:
            default_map = provider_map["default"]
            if isinstance(default_map, dict):
                return default_map.get("primary") or default_map.get("backup")
            elif isinstance(default_map, str):
                return default_map

    # Global fallback
    global_fallback = mirror_map.get("default")
    if isinstance(global_fallback, dict):
        return global_fallback.get("primary") or global_fallback.get("backup")
    elif isinstance(global_fallback, str):
        return global_fallback

    raise ValueError(f"No mirror found for provider={provider}, region={region}")


def build_repo_config(metadata: CloudMetadata, mirror_url: str) -> configparser.ConfigParser:
    """
    Build a repo configuration object using the selected mirror URL.
    """
    config = configparser.ConfigParser()
    section = "base"
    config.add_section(section)
    config.set(section, "name", f"{metadata.provider.upper()} Mirror")
    config.set(section, "baseurl", f"{mirror_url}/{metadata.region}/rocky-lts-$releasever.$basearch")
    config.set(section, "enabled", "1")
    return config
