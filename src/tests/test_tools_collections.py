"""
Tests for collection management tools.
"""

import pytest
from unittest.mock import patch

from writefreely_mcp_server.tools import collections
from writefreely_mcp_server.api_client import WriteAsError


@pytest.fixture
def mock_get_access_token():
    """Mock the get_access_token function."""
    with patch("writefreely_mcp_server.tools.collections.get_access_token") as mock:
        yield mock


@pytest.fixture
def mock_get_user_collections():
    """Mock the get_user_collections function."""
    with patch("writefreely_mcp_server.tools.collections.get_user_collections") as mock:
        yield mock


@pytest.fixture
def mock_get_collection_posts():
    """Mock the get_collection_posts function."""
    with patch("writefreely_mcp_server.tools.collections.get_collection_posts") as mock:
        yield mock


@pytest.fixture
def mock_update_collection():
    """Mock the update_collection function."""
    with patch(
        "writefreely_mcp_server.tools.collections.api_update_collection"
    ) as mock:
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


class TestListMyCollections:
    """Tests for the list_my_collections tool."""

    @pytest.mark.asyncio
    async def test_list_my_collections_success(
        self, mock_get_access_token, mock_get_user_collections
    ):
        """Test successful listing of user collections."""
        mock_get_access_token.return_value = "token123"
        mock_get_user_collections.return_value = [
            {
                "alias": "blog1",
                "title": "Blog 1",
                "description": "First blog",
                "views": 50,
            },
            {
                "alias": "blog2",
                "title": "Blog 2",
                "description": "Second blog",
                "views": 100,
            },
        ]

        tool_func = get_tool_function(collections, "list_my_collections")

        result = await tool_func("token123")
        assert "2 collection(s)" in result
        assert "Blog 1" in result
        assert "Blog 2" in result
        assert "blog1" in result
        assert "blog2" in result

    @pytest.mark.asyncio
    async def test_list_my_collections_empty(
        self, mock_get_access_token, mock_get_user_collections
    ):
        """Test listing collections when user has none."""
        mock_get_access_token.return_value = "token123"
        mock_get_user_collections.return_value = []

        tool_func = get_tool_function(collections, "list_my_collections")

        result = await tool_func("token123")
        assert "no collections found" in result.lower()

    @pytest.mark.asyncio
    async def test_list_my_collections_no_token(self, mock_get_access_token):
        """Test listing collections without token."""
        mock_get_access_token.return_value = None

        tool_func = get_tool_function(collections, "list_my_collections")

        result = await tool_func(None)
        assert "error" in result.lower()
        assert "required" in result.lower()

    @pytest.mark.asyncio
    async def test_list_my_collections_error(
        self, mock_get_access_token, mock_get_user_collections
    ):
        """Test listing collections error handling."""
        mock_get_access_token.return_value = "token123"
        mock_get_user_collections.side_effect = WriteAsError("API Error")

        tool_func = get_tool_function(collections, "list_my_collections")

        result = await tool_func("token123")
        assert "failed" in result.lower()


class TestBrowseCollection:
    """Tests for the browse_collection tool."""

    @pytest.mark.asyncio
    async def test_browse_collection_success(self, mock_get_collection_posts):
        """Test successful collection browsing."""
        mock_get_collection_posts.return_value = [
            {
                "id": "post1",
                "slug": "post-1",
                "title": "Post 1",
                "created": "2024-01-01T00:00:00Z",
                "views": 10,
            },
            {
                "id": "post2",
                "slug": "post-2",
                "title": "Post 2",
                "created": "2024-01-02T00:00:00Z",
                "views": 20,
            },
        ]

        tool_func = get_tool_function(collections, "browse_collection")

        result = await tool_func("myblog", page=1)
        assert "myblog" in result
        assert "Page 1" in result
        assert "2 post(s)" in result
        assert "Post 1" in result
        assert "Post 2" in result
        mock_get_collection_posts.assert_called_once_with("myblog", page=1)

    @pytest.mark.asyncio
    async def test_browse_collection_empty(self, mock_get_collection_posts):
        """Test browsing empty collection."""
        mock_get_collection_posts.return_value = []

        tool_func = get_tool_function(collections, "browse_collection")

        result = await tool_func("myblog", page=1)
        assert "no posts found" in result.lower()

    @pytest.mark.asyncio
    async def test_browse_collection_pagination_hint(self, mock_get_collection_posts):
        """Test pagination hint when 10 posts are returned."""
        mock_get_collection_posts.return_value = [
            {
                "id": f"post{i}",
                "slug": f"post-{i}",
                "title": f"Post {i}",
                "created": "2024-01-01T00:00:00Z",
                "views": 0,
            }
            for i in range(10)
        ]

        tool_func = get_tool_function(collections, "browse_collection")

        result = await tool_func("myblog", page=1)
        assert "page 2" in result.lower()

    @pytest.mark.asyncio
    async def test_browse_collection_error(self, mock_get_collection_posts):
        """Test collection browsing error handling."""
        mock_get_collection_posts.side_effect = WriteAsError("API Error")

        tool_func = get_tool_function(collections, "browse_collection")

        result = await tool_func("myblog", page=1)
        assert "failed" in result.lower()


class TestUpdateCollection:
    """Tests for the update_collection tool."""

    @pytest.mark.asyncio
    async def test_update_collection_success(
        self, mock_get_access_token, mock_update_collection
    ):
        """Test successful collection update."""
        mock_get_access_token.return_value = "token123"
        mock_update_collection.return_value = {
            "alias": "myblog",
            "title": "Updated Blog",
            "description": "Updated description",
            "views": 100,
        }

        tool_func = get_tool_function(collections, "update_collection")

        result = await tool_func(
            "myblog", "token123", "Updated Blog", "Updated description"
        )
        assert "updated successfully" in result.lower()
        assert "Updated Blog" in result
        assert "Updated description" in result
        mock_update_collection.assert_called_once_with(
            alias="myblog",
            access_token="token123",
            title="Updated Blog",
            description="Updated description",
            style_sheet=None,
        )

    @pytest.mark.asyncio
    async def test_update_collection_with_stylesheet(
        self, mock_get_access_token, mock_update_collection
    ):
        """Test updating collection with stylesheet."""
        mock_get_access_token.return_value = "token123"
        mock_update_collection.return_value = {
            "alias": "myblog",
            "title": "My Blog",
            "style_sheet": "body { color: red; }",
        }

        tool_func = get_tool_function(collections, "update_collection")

        result = await tool_func(
            "myblog", "token123", None, None, "body { color: red; }"
        )
        assert "updated successfully" in result.lower()
        mock_update_collection.assert_called_once_with(
            alias="myblog",
            access_token="token123",
            title=None,
            description=None,
            style_sheet="body { color: red; }",
        )

    @pytest.mark.asyncio
    async def test_update_collection_no_token(self, mock_get_access_token):
        """Test updating collection without token."""
        mock_get_access_token.return_value = None

        tool_func = get_tool_function(collections, "update_collection")

        result = await tool_func("myblog", "", None, None, None)
        assert "error" in result.lower()
        assert "required" in result.lower()

    @pytest.mark.asyncio
    async def test_update_collection_error(
        self, mock_get_access_token, mock_update_collection
    ):
        """Test collection update error handling."""
        mock_get_access_token.return_value = "token123"
        mock_update_collection.side_effect = WriteAsError("Update failed")

        tool_func = get_tool_function(collections, "update_collection")

        result = await tool_func("myblog", "token123", "New Title")
        assert "failed" in result.lower()
