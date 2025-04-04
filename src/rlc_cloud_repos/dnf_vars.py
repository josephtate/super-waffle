# src/rlc_cloud_repos/dnf_vars.py
"""
DNF Variable Management for CIQ Cloud Repos

This module sets DNF variables in /etc/dnf/vars required for proper repository
URL construction using system and cloud metadata.

Variables Managed:
- baseurl1: Primary mirror URL
- baseurl2: Global fallback mirror
- region: Cloud region
"""

import logging
from pathlib import Path

DNF_VARS_DIR = Path("/etc/dnf/vars")
BACKUP_SUFFIX = ".bak"

logger = logging.getLogger(__name__)


def _write_dnf_var(name: str, value: str):
    """
    Creates or updates a DNF variable file with a given value.

    - If the file does not exist, it is created with the specified value.
    - If the file exists and contains a different value, it is backed up
      (appending '.bak') before being overwritten.
    - If the file already contains the desired value, no action is taken.

    Args:
        name (str): Name of the DNF variable (e.g., 'region', 'baseurl1').
        value (str): Value to set for the DNF variable.

    Side Effects:
        - Writes to /etc/dnf/vars/
        - Creates .bak files for existing values that are changed
        - Logs all operations
    """
    path = DNF_VARS_DIR / name

    # Ensure /etc/dnf/vars exists
    DNF_VARS_DIR.mkdir(parents=True, exist_ok=True)

    # Check if exists and content differs
    if path.exists():
        current_value = path.read_text().strip()
        if current_value == value:
            logger.debug(f"DNF var '{name}' already set correctly.")
            return
        # Backup
        backup_path = path.with_suffix(path.suffix + BACKUP_SUFFIX)
        path.rename(backup_path)
        logger.info(f"Backed up existing DNF var '{name}' to '{backup_path.name}'")

    try:
        path.write_text(f"{value}\n")
        logger.info(f"Wrote DNF var '{name}': {value}")
    except Exception as e:
        logger.error(f"Cannot write to DNF var '{name}' ({e}), skipping")


def ensure_all_dnf_vars(metadata: dict[str, str], mirror_url: str):
    """
    Sets required DNF variables for building repo baseurls.

    Args:
        metadata (dict[str, str]): Cloud provider and region info.
        mirror_url (str): The selected base mirror URL.
    """
    # Base mirrors
    _write_dnf_var("baseurl1", mirror_url)
    _write_dnf_var("baseurl2", "https://depot.prod.ciqws.com")