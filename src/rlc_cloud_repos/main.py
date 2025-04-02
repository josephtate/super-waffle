# src/rlc_cloud_repos/main.py
"""
RLC Cloud Repo Resolver CLI

This tool detects the cloud provider and region, selects the appropriate
CIQ repository mirror, and optionally writes a .repo configuration file
to /etc/yum.repos.d.

Supports AWS, Azure, GCP, Oracle with override options.

Author: Joel Hanger
Created: 2025-03
License: CIQ Proprietary
"""
import argparse
import logging
import logging.handlers
import sys
import os
from datetime import datetime
from rlc_cloud_repos.cloud_metadata import get_cloud_metadata, CloudMetadata
from rlc_cloud_repos.log_utils import setup_logging, log_and_print, logger
from rlc_cloud_repos.dnf_vars import ensure_all_dnf_vars
from rlc_cloud_repos.repo_config import (
    load_mirror_map,
    select_mirror,
    build_repo_config,
)

DEFAULT_MIRROR_PATH = "/etc/rlc-cloud-repos/ciq-mirrors.yaml"
DEFAULT_OUTPUT_PATH = "/etc/yum.repos.d/rlc-depot.repo"
TOUCHFILE = "/etc/rlc-cloud-repos/.configured"


def check_touchfile() -> None:
    """
    Exit early if the system has already been configured.

    Creates an idempotent barrier to prevent re-running this tool
    automatically after successful configuration.
    """
    if os.path.exists(TOUCHFILE):
        log_and_print(f"Touchfile exists ({TOUCHFILE}). Skipping repo update.")
        sys.exit(0)


def write_touchfile() -> None:
    """
    Create a touchfile to indicate configuration was completed.

    This prevents the repo from being configured more than once automatically.
    """
    os.makedirs(os.path.dirname(TOUCHFILE), exist_ok=True)
    with open(TOUCHFILE, "w") as f:
        f.write(f"Configured on {datetime.now().isoformat()}\n")


def main() -> int:
    """
    Entry point for the CLI utility.

    Parses CLI args, performs metadata detection, resolves repo mirrors,
    and writes repo files if requested.
    """
    setup_logging()
    check_touchfile()

    parser = argparse.ArgumentParser(
        description="RLC Cloud Repo Resolver",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--cloud", help="Override detected cloud", choices=["aws", "azure", "gcp", "oracle"])
    parser.add_argument("--region", help="Override detected region")
    parser.add_argument("--format", choices=["url", "repo"], default="url", help="Output format")
    parser.add_argument("--mirror-file", help="Path to mirror YAML override")
    parser.add_argument(
        "--output",
        nargs="?",
        const=DEFAULT_OUTPUT_PATH,
        help="Write .repo file to disk (default: /etc/yum.repos.d/rlc-depot.repo)"
    )
    args = parser.parse_args()

    # Step 1: Detect or override cloud/region
    metadata: CloudMetadata = get_cloud_metadata()
    log_and_print(f"Using cloud metadata: provider={metadata.provider}, region={metadata.region}")
    if args.cloud:
        metadata.provider = args.cloud
    if args.region:
        metadata.region = args.region

    # Step 2: Load mirror map and select appropriate URL
    mirror_file_path = args.mirror_file or DEFAULT_MIRROR_PATH
    mirror_map = load_mirror_map(mirror_file_path)
    log_and_print(f"Loaded mirror map from {mirror_file_path}")
    mirror_url = select_mirror(metadata, mirror_map)
    log_and_print(f"Selected mirror URL: {mirror_url}")

    # Step 3: Ensure all DNF variables are set
    ensure_all_dnf_vars(metadata, mirror_url)
    logger.info("DNF vars set for region=%s and mirror=%s", metadata.region, mirror_url)
    
    # Step 4: Output repo URL or generate .repo file
    if args.format == "url":
        log_and_print("info", mirror_url)
    else:
        config = build_repo_config(metadata, mirror_url)
        lines = ["[base]"]
        for key, val in config.items("base"):
            lines.append(f"{key}={val}")
        repo_text = "\n".join(lines)

        if args.output:
            output_path = args.output if isinstance(args.output, str) else DEFAULT_OUTPUT_PATH
            try:
                with open(output_path, "w") as f:
                    f.write(repo_text + "\n")
                log_and_print("info", f"Wrote repo to {output_path}")
                write_touchfile()
                log_and_print(f"Touchfile written to {TOUCHFILE}")
            except Exception as e:
                log_and_print("error", f"❌ Failed to write repo file: {e}")
                return 1
        else:
            log_and_print("info", repo_text)
            write_touchfile()
            log_and_print(f"Touchfile written to {TOUCHFILE}")

    return 0


if __name__ == "__main__":
    sys.exit(main())