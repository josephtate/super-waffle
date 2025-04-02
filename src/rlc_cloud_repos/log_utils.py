# src/rlc_cloud_repos/log_utils.py
"""
Logging utility to streamline dual output to syslog and terminal.

Provides: log_and_print()

Author: Joel Hanger
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
