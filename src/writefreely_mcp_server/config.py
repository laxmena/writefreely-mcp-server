import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

WRITEAS_URL = "https://write.as"
READ_WRITEAS_URL = "https://read.write.as"

# Base URL - can be overridden via environment variable
BASE_URL = os.getenv("WRITEFREELY_BASE_URL", WRITEAS_URL)

# Access token - can be provided via environment variable for better security
ACCESS_TOKEN = os.getenv("WRITEFREELY_ACCESS_TOKEN")

# Default timeout for HTTP requests (seconds)
REQUEST_TIMEOUT = 30.0

DEFAULT_LANGUAGE = os.getenv("WRITEFREELY_DEFAULT_LANGUAGE", "en")


def get_base_url() -> str:
    """Get the currently active base URL (allows dynamic override)."""
    return BASE_URL


def get_access_token(provided_token: Optional[str] = None) -> Optional[str]:
    """
    Get access token from provided parameter or environment variable.

    Priority:
    1. Provided token (from tool parameter)
    2. Environment variable WRITEFREELY_ACCESS_TOKEN

    Args:
        provided_token: Optional token provided as a parameter

    Returns:
        Access token string or None if not available
    """
    if provided_token:
        logger.debug("Using access token from provided parameter")
        return provided_token

    env_token = os.getenv("WRITEFREELY_ACCESS_TOKEN")
    if env_token:
        logger.debug(
            "Using access token from WRITEFREELY_ACCESS_TOKEN environment variable"
        )
    else:
        logger.debug("No access token found in environment variable")
    return env_token
