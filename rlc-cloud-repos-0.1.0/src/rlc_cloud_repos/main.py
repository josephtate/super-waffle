import argparse
import sys
import os
from rlc_cloud_repos.cloud_metadata import get_cloud_info, CloudMetadata
from rlc_cloud_repos.repo_config import (
    load_mirror_map,
    select_mirror,
    build_repo_config,
)

DEFAULT_MIRROR_PATH = "/etc/rlc-cloud-repos/mirrors.yaml"
DEFAULT_OUTPUT_PATH = "/etc/yum.repos.d/rlc-depot.repo"

def main():
    parser = argparse.ArgumentParser(description="RLC Cloud Repo Resolver")
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

    # Detect metadata
    metadata = get_cloud_info()
    if args.cloud:
        metadata.provider = args.cloud
    if args.region:
        metadata.region = args.region

    # Load mirrors
    mirror_file_path = args.mirror_file or DEFAULT_MIRROR_PATH
    mirror_map = load_mirror_map(mirror_file_path)
    mirror_url = select_mirror(metadata, mirror_map)

    # Output result
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
            except Exception as e:
                print(f"❌ Failed to write repo file: {e}", file=sys.stderr)
                return 1
        else:
            print(repo_text)

    return 0

if __name__ == "__main__":
    sys.exit(main())