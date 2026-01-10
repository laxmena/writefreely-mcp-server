"""
Shared pytest fixtures for test suite.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_mcp():
    """Create a mock MCP server instance."""
    mcp = MagicMock()
    return mcp
