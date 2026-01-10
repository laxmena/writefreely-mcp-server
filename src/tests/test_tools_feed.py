"""
Tests for feed tools.
"""

import pytest
from unittest.mock import patch

from writefreely_mcp_server.tools import feed
from writefreely_mcp_server.api_client import WriteAsError


@pytest.fixture
def mock_get_read_writeas_posts():
    """Mock the get_read_writeas_posts function."""
    with patch("writefreely_mcp_server.tools.feed.get_read_writeas_posts") as mock:
        yield mock


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


class TestBrowsePublicFeed:
    """Tests for the browse_public_feed tool."""

    @pytest.mark.asyncio
    async def test_browse_public_feed_success(self, mock_get_read_writeas_posts):
        """Test successful public feed browsing."""
        mock_get_read_writeas_posts.return_value = [
            {
                "id": "feed1",
                "slug": "feed-post-1",
                "title": "Feed Post 1",
                "created": "2024-01-01T00:00:00Z",
                "views": 100,
                "collection": None,
            },
            {
                "id": "feed2",
                "slug": "feed-post-2",
                "title": "Feed Post 2",
                "created": "2024-01-02T00:00:00Z",
                "views": 200,
                "collection": {"alias": "myblog"},
            },
        ]

        tool_func = get_tool_function(feed, "browse_public_feed")

        result = await tool_func(skip=0)
        assert "Public Feed" in result
        assert "showing posts 1-2" in result
        assert "Feed Post 1" in result
        assert "Feed Post 2" in result
        assert "Collection: myblog" in result
        mock_get_read_writeas_posts.assert_called_once_with(skip=0)

    @pytest.mark.asyncio
    async def test_browse_public_feed_empty(self, mock_get_read_writeas_posts):
        """Test browsing empty public feed."""
        mock_get_read_writeas_posts.return_value = []

        tool_func = get_tool_function(feed, "browse_public_feed")

        result = await tool_func(skip=0)
        assert "no posts found" in result.lower()

    @pytest.mark.asyncio
    async def test_browse_public_feed_pagination(self, mock_get_read_writeas_posts):
        """Test public feed pagination."""
        mock_get_read_writeas_posts.return_value = [
            {
                "id": f"feed{i}",
                "slug": f"feed-post-{i}",
                "title": f"Feed Post {i}",
                "created": "2024-01-01T00:00:00Z",
                "views": 0,
                "collection": None,
            }
            for i in range(10)
        ]

        tool_func = get_tool_function(feed, "browse_public_feed")

        result = await tool_func(skip=10)
        assert "showing posts 11-20" in result
        assert "skip=20" in result
        mock_get_read_writeas_posts.assert_called_once_with(skip=10)

    @pytest.mark.asyncio
    async def test_browse_public_feed_pagination_hint(
        self, mock_get_read_writeas_posts
    ):
        """Test pagination hint when 10 posts are returned."""
        mock_get_read_writeas_posts.return_value = [
            {
                "id": f"feed{i}",
                "slug": f"feed-post-{i}",
                "title": f"Feed Post {i}",
                "created": "2024-01-01T00:00:00Z",
                "views": 0,
                "collection": None,
            }
            for i in range(10)
        ]

        tool_func = get_tool_function(feed, "browse_public_feed")

        result = await tool_func(skip=0)
        assert "skip=10" in result

    @pytest.mark.asyncio
    async def test_browse_public_feed_with_collection(
        self, mock_get_read_writeas_posts
    ):
        """Test feed browsing with collection info."""
        mock_get_read_writeas_posts.return_value = [
            {
                "id": "feed1",
                "slug": "feed-post-1",
                "title": "Feed Post 1",
                "created": "2024-01-01T00:00:00Z",
                "views": 100,
                "collection": {"alias": "myblog"},
            }
        ]

        tool_func = get_tool_function(feed, "browse_public_feed")

        result = await tool_func(skip=0)
        assert "Collection: myblog" in result

    @pytest.mark.asyncio
    async def test_browse_public_feed_error(self, mock_get_read_writeas_posts):
        """Test public feed browsing error handling."""
        mock_get_read_writeas_posts.side_effect = WriteAsError("API Error")

        tool_func = get_tool_function(feed, "browse_public_feed")

        result = await tool_func(skip=0)
        assert "failed" in result.lower()
