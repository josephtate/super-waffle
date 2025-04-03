# src/rlc_cloud_repos/repo_config.py
import configparser
import logging
import os
import yaml
from pathlib import Path
from shutil import copyfile
from pathlib import Path
from typing import Any, Optional
from rlc_cloud_repos.cloud_metadata import CloudMetadata
from rlc_cloud_repos.log_utils import log_and_print

logger = logging.getLogger(__name__)


def load_mirror_map(yaml_path: Optional[str] = None) -> dict[str, Any]:
    """
    Loads the YAML mirror map config.

    Args:
        yaml_path (str, optional): Custom path to YAML config.

    Returns:
        dict[str, Any]: Mirror map dictionary.

    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If YAML is invalid.
    """
    yaml_path = (
        yaml_path or
        os.getenv("RLC_MIRROR_MAP_PATH") or
        "/etc/rlc-cloud-repos/ciq-mirrors.yaml"
    )
    path = Path(yaml_path)

    if not path.exists():
        logger.error("Mirror YAML not found at %s", yaml_path)
        raise FileNotFoundError(f"Mirror config YAML not found at {yaml_path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.exception("YAML parsing error")
        raise ValueError(f"Invalid YAML in mirror map: {e}")


def select_mirror(metadata: CloudMetadata, mirror_map: dict[str, Any]) -> str:
    """
    Chooses the best mirror URL for the given cloud metadata.

    Args:
        metadata (CloudMetadata): Cloud region + provider info.
        mirror_map (dict): Parsed YAML mirror map.

    Returns:
        str: Selected mirror URL.

    Raises:
        ValueError: If no usable mirror is found.
    """
    provider = metadata.provider.lower()
    region = metadata.region

    logger.info("Selecting mirror for provider=%s, region=%s", provider, region)

    provider_map = mirror_map.get(provider, {})

    if isinstance(provider_map, dict):
        region_map = provider_map.get(region)
        if isinstance(region_map, dict):
            return region_map.get("primary") or region_map.get("backup")

        default_map = provider_map.get("default")
        if isinstance(default_map, dict):
            return default_map.get("primary") or default_map.get("backup")
        elif isinstance(default_map, str):
            return default_map

    fallback = mirror_map.get("default")
    if isinstance(fallback, dict):
        return fallback.get("primary") or fallback.get("backup")
    elif isinstance(fallback, str):
        return fallback

    logger.error("No mirror found for provider=%s, region=%s", provider, region)
    raise ValueError(f"No mirror found for provider={provider}, region={region}")


def install_default_repo_file(
    template_path: Path = Path("/etc/rlc-cloud-repos/ciq-depot.repo"),
    dest_path: Path = Path("/etc/yum.repos.d/ciq-depot.repo")
):
    """
    Installs the default CIQ repo file into /etc/yum.repos.d/.
    If one exists, backs it up. Uses static template from /etc/rlc-cloud-repos/.
    
    Args:
        template_path (Path): Source repo file template (default system location)
        dest_path (Path): Destination .repo path (default yum.repos.d)
    """
    backup_path = dest_path.with_suffix(dest_path.suffix + ".bak")

    if not template_path.exists():
        log_and_print(f"❌ Missing default repo template at {template_path}", level="error")
        return

    if dest_path.exists():
        log_and_print(f"🛑 Repo file already exists: {dest_path}, backing up to {backup_path}")
        copyfile(dest_path, backup_path)
    else:
        log_and_print(f"✅ No existing repo found. Proceeding to install {dest_path}")

    copyfile(template_path, dest_path)
    log_and_print(f"📦 Installed default repo file to {dest_path}")


# DEPRECTATED: Remove after refactoring
def build_repo_config(metadata: CloudMetadata, mirror_url: str) -> configparser.ConfigParser:
    """
    Constructs a YUM repo config object using the mirror URL.

    Args:
        metadata (CloudMetadata): Provider/region for naming.
        mirror_url (str): Selected mirror base URL.

    Returns:
        configparser.ConfigParser: Section with repo data.
    """
    config = configparser.ConfigParser()
    section = "base"
    config.add_section(section)
    config.set(section, "name", f"{metadata.provider.upper()} Mirror")
    config.set(section, "baseurl", f"{mirror_url}/{metadata.region}/rocky-lts-$releasever.$basearch")
    config.set(section, "enabled", "1")
    logger.debug("Built repo config for provider=%s", metadata.provider)
    return config