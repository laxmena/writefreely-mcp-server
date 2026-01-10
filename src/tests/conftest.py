"""
Shared pytest fixtures for test suite.
"""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_mcp():
    """Create a mock MCP server instance."""
    mcp = MagicMock()
    return mcp
