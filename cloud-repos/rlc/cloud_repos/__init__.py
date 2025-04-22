from pkg_resources import get_distribution

try:
    __version__ = get_distribution("rlc.cloud-repos").version
except Exception:  # pragma: no cover
    __version__ = "unknown"
