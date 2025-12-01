"""Minimal logger setup used across the CLI.

The goal is to avoid noisy output for users while still enabling debug
troubleshooting via an environment variable.
"""

from __future__ import annotations

import logging
import os

LOG_LEVEL = os.getenv("AFFINITY_CLI_LOG", "INFO").upper()

logger = logging.getLogger("affinity_cli")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

__all__ = ["logger"]
