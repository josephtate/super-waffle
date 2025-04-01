# src/rlc_cloud_repos/cloud_metadata.py
"""
RLC Cloud Repos - Configuration and Cloud Metadata Logic

This module handles:
- Parsing YAML mirror maps
- Selecting the best repo mirror based on cloud metadata
- Generating .repo-style YUM config sections
- Extracting cloud environment metadata from cloud-init
"""

import logging
import os
import json
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class CloudMetadata:
    """
    Data structure representing the cloud instance's environment.

    Attributes:
        provider (str): Name of the cloud provider (e.g., aws, azure).
        region (str): Region in which the instance is running.
        instance_id (str): Instance identifier.
        additional_info (dict): Optional additional metadata.
    """
    def __init__(self, provider: str, region: str, instance_id: str, additional_info: dict = None):
        self.provider = provider
        self.region = region
        self.instance_id = instance_id
        self.additional_info = additional_info or {}

    def __repr__(self) -> str:
        return (
            f"CloudMetadata(provider={self.provider}, region={self.region}, "
            f"instance_id={self.instance_id}, additional_info={self.additional_info})"
        )


def _query_cloud_init_fallback() -> dict[str, Optional[str]]:
    """
    Fallback metadata detection via cloud-init CLI.

    Returns:
        dict[str, Optional[str]]: keys like 'provider', 'region', 'instance_id'
    """
    def query(key: str) -> Optional[str]:
        try:
            return subprocess.check_output(["cloud-init", "query", key], text=True).strip()
        except Exception as e:
            logger.warning("Fallback: failed to get '%s' via cloud-init query: %s", key, e)
            return None

    return {
        "provider": query("v1.cloud_name") or "unknown",
        "region": query("v1.region"),
        "instance_id": query("v1.instance_id") or "unknown",
    }


def get_cloud_metadata() -> CloudMetadata:
    """
    Detects the cloud environment and extracts metadata.

    Returns:
        CloudMetadata: Populated metadata object.

    Raises:
        FileNotFoundError: If cloud-init metadata is not found.
        ValueError: If the metadata JSON is invalid.
    """
    metadata_file = os.getenv("RLC_METADATA_PATH", "/run/cloud-init/instance-data.json")
    metadata_path = Path(metadata_file)

    if not metadata_path.exists():
        logger.warning("JSON metadata file not found; falling back to cloud-init CLI")
        fallback = _query_cloud_init_fallback()
        return CloudMetadata(
            provider=fallback["provider"],
            region=fallback["region"],
            instance_id=fallback["instance_id"],
            additional_info={}
        )

    try:
        with metadata_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.warning("Invalid JSON in cloud-init file; falling back to CLI: %s", e)
        fallback = _query_cloud_init_fallback()
        return CloudMetadata(
            provider=fallback["provider"],
            region=fallback["region"],
            instance_id=fallback["instance_id"],
            additional_info={}
        )

    # Attempt to extract metadata from traditional ds.metadata
    ds_metadata = data.get("ds", {}).get("metadata")

    # Fallback: AWS-style metadata from dynamic.instance-identity.document
    dynamic_doc = (
        data.get("ds", {})
            .get("dynamic", {})
            .get("instance-identity", {})
            .get("document", {})
    )

    # Initial extraction
    provider = ds_metadata.get("cloud_name") if ds_metadata else None
    region = None
    instance_id = None

    if ds_metadata:
        region = (
            ds_metadata.get("region") or
            ds_metadata.get("location") or
            ds_metadata.get("availabilityDomain")
        )
        instance_id = ds_metadata.get("instance_id")

    # Check dynamic document if needed
    if not region:
        region = dynamic_doc.get("region")
    if not instance_id:
        instance_id = dynamic_doc.get("instanceId")

    # Check v1 fallback for provider
    if not provider:
        provider = data.get("v1", {}).get("cloud_name")

    # Fallback to CLI if still missing
    if not provider or not region:
        logger.warning("Missing provider or region; using CLI fallback")
        fallback = _query_cloud_init_fallback()
        return CloudMetadata(
            provider=fallback["provider"],
            region=fallback["region"],
            instance_id=fallback["instance_id"],
            additional_info=ds_metadata or dynamic_doc
        )

    logger.info("Detected metadata: provider=%s, region=%s", provider, region)

    return CloudMetadata(
        provider=provider,
        region=region,
        instance_id=instance_id or "unknown",
        additional_info=ds_metadata or dynamic_doc
    )