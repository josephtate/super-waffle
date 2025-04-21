# src/rlc_cloud_repos/repo_config.py
import logging
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml

logger = logging.getLogger(__name__)


def load_mirror_map(yaml_path: str) -> Dict[str, Any]:
    """
    Loads the YAML mirror map config.

    Args:
        yaml_path (str): Path to YAML config.

    Returns:
        Dict[str, Any]: Mirror map dictionary.

    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If YAML is invalid.
    """
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


def select_mirror(metadata: Dict[str, str],
                  mirror_map: Dict[str, Any]) -> Tuple[str, str]:
    """
    Chooses the best primary and backup mirror URLs for the given cloud metadata.

    Returns:
        tuple[str, str]: (primary_url, backup_url)
    """
    provider = metadata["provider"].lower()
    region = metadata["region"]

    # Set up our fallback fallbacks
    # We do not use default values here because we want this to fail in tests if we have a bad file. We must always have a default with primary and backup values set.
    default_primary = mirror_map.get("default").get("primary")
    default_backup = mirror_map.get("default").get("backup")

    logger.info("Selecting mirror for provider=%s, region=%s", provider,
                region)

    if provider in mirror_map:
        provider_map = mirror_map[provider]
        if region in provider_map:
            region_map = provider_map.get(region, {})
        else:
            region_map = provider_map.get("default", {})
        return region_map.get("primary", default_primary), region_map.get(
            "backup", default_backup)

    else:
        logger.debug("Provider %s not found, using default values", provider)
        return default_primary, default_backup
