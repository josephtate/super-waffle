# src/rlc_cloud_repos/dnf_vars.py
"""
DNF Variable Management for CIQ Cloud Repos

This module sets DNF variables in /etc/dnf/vars required for proper repository
URL construction using system and cloud metadata.

Variables Managed:
- baseurl1: Primary mirror URL
- baseurl2: Global fallback mirror
- region: Cloud region
- infra: Infrastructure type (e.g., ec2, azure)
- rltype: Rocky Linux release type (rl8, rl9, etc.)
- contentdir: Base content directory (typically 'pub/rocky')
- sigcontentdir: SIG-specific content path (typically 'pub/sig')
"""

import logging
import re
from pathlib import Path
from rlc_cloud_repos.cloud_metadata import CloudMetadata

DNF_VARS_DIR = Path("/etc/dnf/vars")

logger = logging.getLogger(__name__)


def _write_dnf_var(name: str, value: str):
    """Writes a single DNF variable if it doesn't already exist."""
    path = DNF_VARS_DIR / name
    if path.exists():
        return
    DNF_VARS_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{value}\n")


def _parse_rocky_release() -> str:
    """
    Determines the Rocky Linux release type from /etc/rocky-release.

    Returns:
        str: e.g., 'rl9' or 'rl8'
    """
    rocky_file = Path("/etc/rocky-release")
    if not rocky_file.exists():
        return "rl-unknown"

    match = re.search(r"Rocky Linux release (\d+)", rocky_file.read_text())
    return f"rl{match.group(1)}" if match else "rl-unknown"


def _parse_stream_version() -> str:
    """
    Determines stream version from /etc/os-release or fallback.

    Returns:
        str: e.g., '9-stream'
    """
    os_release = Path("/etc/os-release")
    if not os_release.exists():
        return "9-stream"

    for line in os_release.read_text().splitlines():
        if line.startswith("VERSION_ID="):
            return line.split("=")[1].strip('"') + "-stream"
    return "9-stream"


def ensure_all_dnf_vars(metadata: CloudMetadata, mirror_url: str):
    """
    Sets required DNF variables for building repo baseurls.

    Args:
        metadata (CloudMetadata): Cloud provider and region data.
        mirror_url (str): The selected base mirror URL.
    """
    # Base mirrors
    _write_dnf_var("baseurl1", mirror_url)
    _write_dnf_var("baseurl2", mirror_url.rsplit(".", 1)[0] + ".prod.ciqws.com")

    # Region and cloud type
    _write_dnf_var("region", metadata.region or "unknown")
    _write_dnf_var("infra", metadata.provider or "unknown")

    # Rocky release and layout
    _write_dnf_var("rltype", _parse_rocky_release())
    _write_dnf_var("contentdir", "pub/rocky")
    _write_dnf_var("sigcontentdir", "pub/sig")
