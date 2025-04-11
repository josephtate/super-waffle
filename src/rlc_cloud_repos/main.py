# src/rlc_cloud_repos/main.py
"""
RLC Cloud Repo Resolver CLI

This tool detects the cloud provider and region via cloud-init,
selects the appropriate CIQ repository mirror, and writes DNF vars
for optimized regional repo access.
"""

import argparse
import logging
import sys
import os
from datetime import datetime

from rlc_cloud_repos.cloud_metadata import get_cloud_metadata
from rlc_cloud_repos.log_utils import (
    setup_logging, 
    log_and_print, 
    logger
)
from rlc_cloud_repos.dnf_vars import ensure_all_dnf_vars
from rlc_cloud_repos.repo_config import (
    load_mirror_map, 
    select_mirror, 
    DEFAULT_MIRROR_PATH, 
    MARKERFILE
)


def check_touchfile() -> None:
    """
    Exit early if the system has already been configured.
    Creates an idempotent barrier to prevent re-running this tool.
    """
    if os.path.exists(MARKERFILE):
        log_and_print(f"Marker file exists ({MARKERFILE}). Skipping repo update.")
        sys.exit(0)


def write_touchfile() -> None:
    """
    Create a touchfile to indicate configuration was completed.
    Prevents automatic reruns on reboot (cloud-init idempotency).
    """
    os.makedirs(os.path.dirname(MARKERFILE), exist_ok=True)
    with open(MARKERFILE, "w") as f:
        f.write(f"Configured on {datetime.now().isoformat()}\n")


def _configure_repos(mirror_file_path: str) -> None:
    """
    Core logic for detecting metadata, selecting mirrors, and configuring DNF vars.
    """
    # Detect provider + region via cloud-init query
    metadata = get_cloud_metadata()
    provider = metadata["provider"]
    region = metadata["region"]
    log_and_print(f"Using cloud metadata: provider={provider}, region={region}")

    # Load mirror map + resolve appropriate URL
    mirror_map = load_mirror_map(mirror_file_path)
    log_and_print(f"Loaded mirror map from {mirror_file_path}")

    primary_url, backup_url = select_mirror({"provider": provider, "region": region}, mirror_map)
    log_and_print(f"Selected mirror URL: {primary_url}")

    # Set DNF vars
    ensure_all_dnf_vars(primary_url, backup_url)
    logger.info("DNF vars set for mirror=%s and backup=%s", primary_url, backup_url)

    # Create marker file to prevent future reruns
    write_touchfile()
    log_and_print(f"Marker file written to {MARKERFILE}")


def main() -> int:
    """
    Entry point for RLC cloud repo resolver. Handles argument parsing and
    calls the core configuration logic.
    """
    setup_logging()

    parser = argparse.ArgumentParser(
        description="RLC Cloud Repo Resolver",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--mirror-file", help="Override path to mirror map YAML")
    parser.add_argument("--force", action="store_true", help="Force reconfiguration (ignore marker file)")
    args = parser.parse_args()

    if not args.force:
        check_touchfile() # Exits if already configured

    mirror_path = args.mirror_file or DEFAULT_MIRROR_PATH
    try:
        _configure_repos(mirror_path)
        return 0
    except Exception as e:
        logger.error("Configuration failed: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
