"""
Main MCP server entry point for WriteFreely integration.
Exposes API operations as MCP tools for AI agents.

Supports both self-hosted WriteFreely instances and the Write.as hosted service.
"""

import logging
import os

from mcp.server.fastmcp import FastMCP

from .config import BASE_URL
from .tools import auth, posts, collections, feed

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    # Create the MCP server instance
    mcp = FastMCP(name="writefreely")

    # Register a simple test tool
    @mcp.tool()
    async def hello_writefreely() -> str:
        """
        Simple test tool - confirms the WriteFreely MCP server is running.
        """
        return (
            f"Hello from WriteFreely MCP server!\n"
            f"Base URL: {BASE_URL}\n"
            f"Try login(), publish_post(), or read_post() next."
        )

    # Register all tools from their respective modules
    logger.info("Registering MCP tools...")
    auth.register_tools(mcp)
    posts.register_tools(mcp)
    collections.register_tools(mcp)
    feed.register_tools(mcp)
    logger.info("All tools registered successfully")

    logger.info(f"Starting WriteFreely MCP server (Base URL: {BASE_URL})")
    logger.info("Connect using MCP client (stdio, websocket, etc.)")

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
