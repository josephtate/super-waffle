# src/rlc_cloud_repos/main.py
"""
RLC Cloud Repo Resolver CLI

This tool detects the cloud provider and region, selects the appropriate
CIQ repository mirror, and optionally writes a .repo configuration file
to /etc/yum.repos.d.

Supports AWS, Azure, GCP, Oracle with override options.

Author: Your Name
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
from rlc_cloud_repos.repo_config import (
    load_mirror_map,
    select_mirror,
    build_repo_config,
)

DEFAULT_MIRROR_PATH = "/etc/rlc-cloud-repos/ciq-mirrors.yaml"
DEFAULT_OUTPUT_PATH = "/etc/yum.repos.d/rlc-depot.repo"
TOUCHFILE = "/etc/rlc-cloud-repos/.configured"

# --- Logger Setup ---
logger = logging.getLogger("rlc-cloud-repos")

def check_touchfile() -> None:
    """
    Exit early if the system has already been configured.

    Creates an idempotent barrier to prevent re-running this tool
    automatically after successful configuration.
    """
    if os.path.exists(TOUCHFILE):
        print(f"[INFO] Touchfile exists ({TOUCHFILE}). Skipping repo update.")
        sys.exit(0)


def write_touchfile() -> None:
    """
    Create a touchfile to indicate configuration was completed.

    This prevents the repo from being configured more than once automatically.
    """
    os.makedirs(os.path.dirname(TOUCHFILE), exist_ok=True)
    with open(TOUCHFILE, "w") as f:
        f.write(f"Configured on {datetime.now().isoformat()}\n")


def setup_logging(debug: bool = False) -> None:
    """
    Configure logging to syslog by default, with optional console output for debugging.
    """
    logger = logging.getLogger("rlc-cloud-repos")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Syslog handler (journald or /dev/log)
    try:
        syslog_address = "/dev/log" if sys.platform != "darwin" else "/var/run/syslog"
        syslog_handler = logging.handlers.SysLogHandler(address=syslog_address)
        syslog_format = logging.Formatter("rlc-cloud-repos: [%(levelname)s] %(message)s")
        syslog_handler.setFormatter(syslog_format)
        logger.addHandler(syslog_handler)
    except Exception as e:
        # Fallback if syslog isn't available (e.g., inside containers)
        logging.basicConfig(level=logging.INFO)
        logger.warning("Syslog unavailable, falling back to stderr")

    if debug:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        logger.addHandler(console_handler)


def main() -> int:
    """
    Entry point for the CLI utility.

    Parses CLI args, performs metadata detection, resolves repo mirrors,
    and writes repo files if requested.
    """
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
    if args.cloud:
        metadata.provider = args.cloud
    if args.region:
        metadata.region = args.region

    # Step 2: Load mirror map and select appropriate URL
    mirror_file_path = args.mirror_file or DEFAULT_MIRROR_PATH
    mirror_map = load_mirror_map(mirror_file_path)
    mirror_url = select_mirror(metadata, mirror_map)

    # Step 3: Output repo URL or generate .repo file
    if args.format == "url":
        print(mirror_url)
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
                print(f"Wrote repo to {output_path}")
                write_touchfile()
            except Exception as e:
                print(f"❌ Failed to write repo file: {e}", file=sys.stderr)
                return 1
        else:
            print(repo_text)
            write_touchfile()

    return 0


if __name__ == "__main__":
    sys.exit(main())