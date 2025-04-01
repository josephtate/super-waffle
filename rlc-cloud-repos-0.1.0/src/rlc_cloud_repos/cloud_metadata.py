from pathlib import Path
import json
import os

class CloudMetadata:
    def __init__(self, provider, region, instance_id, additional_info=None):
        self.provider = provider
        self.region = region
        self.instance_id = instance_id
        self.additional_info = additional_info or {}

    def __repr__(self):
        return (f"CloudMetadata(provider={self.provider}, region={self.region}, "
                f"instance_id={self.instance_id}, additional_info={self.additional_info})")


def get_cloud_metadata():
    metadata_file = os.getenv("RLC_METADATA_PATH", "/run/cloud-init/instance-data.json")
    metadata_path = Path(metadata_file)

    if not metadata_path.exists():
        raise FileNotFoundError(f"cloud-init metadata file not found at {metadata_file}")

    try:
        with metadata_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in cloud-init metadata file: {e}")

    ds_metadata = data.get("ds", {}).get("metadata", {})

    provider = ds_metadata.get("cloud_name", "unknown")
    region = (
        ds_metadata.get("region") or
        ds_metadata.get("location") or
        ds_metadata.get("availabilityDomain")
    )
    instance_id = ds_metadata.get("instance_id", "unknown")

    return CloudMetadata(
        provider=provider,
        region=region,
        instance_id=instance_id,
        additional_info=ds_metadata  # or leave this out if not needed
    )
