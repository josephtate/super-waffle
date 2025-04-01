import os
from pathlib import Path
import configparser

from rlc_cloud_repos.cloud_metadata import get_cloud_metadata
from rlc_cloud_repos.repo_config import (
    load_mirror_map,
    select_mirror,
    build_repo_config,
)

# Auto-set test fixtures if not overridden
FIXTURES_DIR = Path(__file__).parent / "fixtures"

os.environ.setdefault("RLC_METADATA_PATH", str(FIXTURES_DIR / "mock-instance-data.json"))
os.environ.setdefault("RLC_MIRROR_MAP_PATH", str(FIXTURES_DIR / "mock-mirrors.yaml"))

def main():
    # Optional: override metadata or mirror map for local testing
    metadata_path = os.getenv("RLC_METADATA_PATH")
    mirror_map_path = os.getenv("RLC_MIRROR_MAP_PATH")

    if not os.getenv("RLC_METADATA_PATH"):
        os.environ["RLC_METADATA_PATH"] = str(Path(__file__).parent / "fixtures" / "mock-instance-data.json")

    if not os.getenv("RLC_MIRROR_MAP_PATH"):
        os.environ["RLC_MIRROR_MAP_PATH"] = str(Path(__file__).parent / "fixtures" / "mock-mirrors.yaml")

    print("🔍 Reading cloud-init metadata...")
    metadata = get_cloud_metadata()

    print(f"🧠 Got metadata: provider={metadata.provider}, region={metadata.region}, instance_id={metadata.instance_id}")
    
    print("📦 Loading mirror map...")
    mirror_map = load_mirror_map(mirror_map_path)

    print("🌍 Selecting mirror...")
    mirror_url = select_mirror(metadata, mirror_map)
    print(f"✅ Selected mirror: {mirror_url}")

    print("🛠️  Building repo config...")
    repo_config = build_repo_config(metadata, mirror_url)

    output_path = Path("/tmp/test.repo")
    with output_path.open("w") as f:
        repo_config.write(f)

    print(f"📄 Repo config written to: {output_path}")
    print(output_path.read_text())


if __name__ == "__main__":
    main()
