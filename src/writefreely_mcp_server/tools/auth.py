"""
Authentication tools for WriteFreely MCP server.
"""

import logging

from ..api_client import authenticate
from ..config import get_access_token

logger = logging.getLogger(__name__)


def register_tools(mcp):
    """Register authentication tools with the MCP server."""

    @mcp.tool()
    async def login(username: str = "", password: str = "") -> str:
        """
        Authenticate with WriteFreely and obtain an access token.

        If WRITEFREELY_ACCESS_TOKEN environment variable is set, this tool will use
        that token automatically without requiring username and password.
        You can provide username and password to authenticate with a different account,
        or use the environment variable for better security (recommended for production).

        Args:
            username: Your WriteFreely username (optional if WRITEFREELY_ACCESS_TOKEN is set)
            password: Your WriteFreely password (optional if WRITEFREELY_ACCESS_TOKEN is set)

        Returns:
            Success message with access token, or information about existing token
        """
        # Check if token is already available from environment
        existing_token = get_access_token()
        if existing_token:
            logger.info(
                "Using access token from WRITEFREELY_ACCESS_TOKEN environment variable"
            )
            return (
                "Access token is already configured via WRITEFREELY_ACCESS_TOKEN "
                "environment variable. Using existing token for authentication.\n"
                "If you want to use a different account, provide username and password "
                "or unset the environment variable first."
            )

        # If no token in environment, require username and password
        if not username or not password:
            logger.warning(
                "Login attempted without credentials and no token in environment"
            )
            return (
                "Error: Username and password are required when WRITEFREELY_ACCESS_TOKEN "
                "is not set in the environment.\n"
                "Either provide username and password, or set WRITEFREELY_ACCESS_TOKEN "
                "environment variable."
            )

        logger.debug(f"Attempting authentication for user: {username}")
        token = await authenticate(username, password)
        if token:
            logger.info(f"Authentication successful for user: {username}")
            return (
                f"Authentication successful. Access token: {token}\n"
                "Note: For better security, consider setting WRITEFREELY_ACCESS_TOKEN "
                "environment variable instead of using this tool."
            )
        else:
            logger.warning(f"Authentication failed for user: {username}")
            return "Authentication failed. Check username and password."
