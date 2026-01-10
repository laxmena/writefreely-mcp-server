"""
Tests for authentication tools.
"""

import pytest
from unittest.mock import patch

from writefreely_mcp_server.tools import auth


def get_tool_function(module, tool_name):
    """Helper to extract a tool function from a module."""
    captured_tools = {}

    def tool_decorator(self):
        # Called as @mcp.tool() - return a decorator
        def decorator(f):
            if hasattr(f, "__name__"):
                captured_tools[f.__name__] = f
            return f

        return decorator

    mock_mcp = type("MockMCP", (), {"tool": tool_decorator})()
    module.register_tools(mock_mcp)
    return captured_tools.get(tool_name)


@pytest.fixture
def mock_authenticate():
    """Mock the authenticate function."""
    with patch("writefreely_mcp_server.tools.auth.authenticate") as mock:
        yield mock


@pytest.fixture
def mock_get_access_token():
    """Mock the get_access_token function."""
    with patch("writefreely_mcp_server.tools.auth.get_access_token") as mock:
        yield mock


class TestLoginTool:
    """Tests for the login tool."""

    @pytest.mark.asyncio
    async def test_login_with_existing_token(self, mock_get_access_token):
        """Test login when token already exists in environment."""
        mock_get_access_token.return_value = "existing_token_123"

        login_func = get_tool_function(auth, "login")
        result = await login_func("", "")

        assert "already configured" in result.lower()
        assert "WRITEFREELY_ACCESS_TOKEN" in result

    @pytest.mark.asyncio
    async def test_login_without_credentials(
        self, mock_get_access_token, mock_authenticate
    ):
        """Test login without credentials when no token in environment."""
        mock_get_access_token.return_value = None

        login_func = get_tool_function(auth, "login")
        result = await login_func("", "")

        assert "error" in result.lower() or "required" in result.lower()

    @pytest.mark.asyncio
    async def test_login_success(self, mock_get_access_token, mock_authenticate):
        """Test successful login."""
        mock_get_access_token.return_value = None
        mock_authenticate.return_value = "new_token_456"

        login_func = get_tool_function(auth, "login")
        result = await login_func("testuser", "testpass")

        assert "successful" in result.lower()
        assert "new_token_456" in result
        mock_authenticate.assert_called_once_with("testuser", "testpass")

    @pytest.mark.asyncio
    async def test_login_failure(self, mock_get_access_token, mock_authenticate):
        """Test login failure."""
        mock_get_access_token.return_value = None
        mock_authenticate.return_value = ""  # Empty token indicates failure

        login_func = get_tool_function(auth, "login")
        result = await login_func("testuser", "wrongpass")

        assert "failed" in result.lower()
