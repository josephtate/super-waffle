# src/rlc_cloud_repos/log_utils.py
"""
Logging utility for cloud-init-friendly stdout/stderr output.

Provides: log_and_print()
"""

import logging
import sys

logger = logging.getLogger("rlc-cloud-repos")


def log_and_print(msg: str, level: str = "info") -> None:
    """
    Logs a message and prints it to stdout or stderr depending on level.

    Args:
        msg (str): The message to emit.
        level (str): One of 'info', 'warn', 'error'. Default is 'info'.
    """
    if level == "info":
        logger.info(msg)
        print(msg)
    elif level in ("warn", "warning"):
        logger.warning(msg)
        print(f"⚠️ {msg}")
    elif level == "error":
        logger.error(msg)
        print(f"❌ {msg}", file=sys.stderr)


def setup_logging(debug: bool = False) -> None:
    """
    Configure logging to emit to stdout/stderr only.

    This aligns with cloud-init expectations (no syslog).
    """
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Avoid adding duplicate handlers
    if logger.hasHandlers():
        return

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    stream_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(stream_handler)
