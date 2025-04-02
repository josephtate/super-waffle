# src/rlc_cloud_repos/log_utils.py
"""
Logging utility to streamline dual output to syslog and terminal.

Provides: log_and_print()

Author: Joel Hanger
"""

import logging
import sys

try:
    from systemd.journal import JournalHandler
except ImportError:
    JournalHandler = None  # fallback handled below

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
    Configure logging to systemd journal if available, otherwise fallback to syslog or stderr.
    """
    global logger
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Only add handlers once
    if logger.hasHandlers():
        return

    if JournalHandler:
        handler = JournalHandler()
        handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        handler._extra["SYSLOG_IDENTIFIER"] = "rlc-cloud-repos"
        logger.addHandler(handler)
    else:
        # Fallback to /dev/log syslog (tagged with 'rlc-cloud-repos')
        try:
            syslog_address = "/dev/log" if sys.platform != "darwin" else "/var/run/syslog"
            syslog_handler = logging.handlers.SysLogHandler(address=syslog_address)
            syslog_handler.ident = 'rlc-cloud-repos: '
            syslog_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
            logger.addHandler(syslog_handler)
        except Exception:
            logging.basicConfig(level=logging.INFO)
            logger.warning("Syslog unavailable, falling back to stderr")

    if debug:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        logger.addHandler(console_handler)
