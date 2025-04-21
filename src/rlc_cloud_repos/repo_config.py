# src/rlc_cloud_repos/repo_config.py
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

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

    logger.info("Selecting mirror for provider=%s, region=%s", provider,
                region)

    provider_map = mirror_map.get(provider, {})
    if isinstance(provider_map, dict):
        region_map = provider_map.get(region)
        if isinstance(region_map, dict):
            return region_map.get("primary", ""), region_map.get("backup", "")

        default_map = provider_map.get("default")
        if isinstance(default_map, dict):
            return default_map.get("primary",
                                   ""), default_map.get("backup", "")
        elif isinstance(default_map, str):
            return default_map, ""

    fallback = mirror_map.get("default")
    if isinstance(fallback, dict):
        return fallback.get("primary", ""), fallback.get("backup", "")
    elif isinstance(fallback, str):
        return fallback, ""

    logger.error("No mirror found for provider=%s, region=%s", provider,
                 region)
    raise ValueError(
        f"No mirror found for provider={provider}, region={region}")
