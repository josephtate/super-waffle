# src/rlc_cloud_repos/cloud_metadata.py

"""
RLC Cloud Repos - Cloud Metadata Detection

Extracts normalized cloud provider and region from cloud-init query.
"""

import logging
import subprocess

logger = logging.getLogger(__name__)


from typing import Dict

def get_cloud_metadata() -> Dict[str, str]:
    """
    Detects the cloud environment using cloud-init's query tool.

    Returns:
        dict[str, str]: Dictionary with keys 'provider' and 'region'

    Raises:
        RuntimeError: If cloud-init query fails.
    """
    try:
        provider = subprocess.check_output(
            ["cloud-init", "query", "cloud_name"], text=True
        ).strip()
        region = subprocess.check_output(
            ["cloud-init", "query", "region"], text=True
        ).strip()
        return {"provider": provider, "region": region}
    except subprocess.CalledProcessError as e:
        logger.error("Failed to query cloud-init: %s", e)
        raise RuntimeError("cloud-init must be available and functional")
