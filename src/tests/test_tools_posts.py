"""
Tests for post management tools.
"""

import pytest
from unittest.mock import patch

from writefreely_mcp_server.tools import posts
from writefreely_mcp_server.api_client import WriteAsError


@pytest.fixture
def mock_get_access_token():
    """Mock the get_access_token function."""
    with patch("writefreely_mcp_server.tools.posts.get_access_token") as mock:
        yield mock


@pytest.fixture
def mock_create_post():
    """Mock the create_post function."""
    with patch("writefreely_mcp_server.tools.posts.create_post") as mock:
        yield mock


@pytest.fixture
def mock_create_collection_post():
    """Mock the create_collection_post function."""
    with patch("writefreely_mcp_server.tools.posts.create_collection_post") as mock:
        yield mock


@pytest.fixture
def mock_get_post():
    """Mock the get_post function."""
    with patch("writefreely_mcp_server.tools.posts.get_post") as mock:
        yield mock


@pytest.fixture
def mock_update_post():
    """Mock the update_post function."""
    with patch("writefreely_mcp_server.tools.posts.update_post") as mock:
        yield mock


@pytest.fixture
def mock_delete_post():
    """Mock the delete_post function."""
    with patch("writefreely_mcp_server.tools.posts.api_delete_post") as mock:
        yield mock


@pytest.fixture
def mock_get_user_posts():
    """Mock the get_user_posts function."""
    with patch("writefreely_mcp_server.tools.posts.get_user_posts") as mock:
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


class TestPublishPost:
    """Tests for the publish_post tool."""

    @pytest.mark.asyncio
    async def test_publish_post_anonymous(
        self, mock_get_access_token, mock_create_post
    ):
        """Test publishing an anonymous post."""
        mock_get_access_token.return_value = None
        mock_create_post.return_value = {
            "id": "post123",
            "slug": "test-post",
            "token": "edit_token_123",
            "body": "Test content",
            "title": "Test Title",
        }

        tool_func = get_tool_function(posts, "publish_post")

        result = await tool_func("Test content", "Test Title")
        assert "created successfully" in result.lower()
        assert "post123" in result
        assert "edit_token_123" in result
        mock_create_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_post_to_collection(
        self, mock_get_access_token, mock_create_collection_post
    ):
        """Test publishing a post to a collection."""
        mock_get_access_token.return_value = "token123"
        mock_create_collection_post.return_value = {
            "id": "post456",
            "slug": "collection-post",
            "body": "Collection content",
            "title": "Collection Title",
        }

        tool_func = get_tool_function(posts, "publish_post")

        result = await tool_func(
            "Collection content", "Collection Title", "token123", "myblog"
        )
        assert "created successfully" in result.lower()
        assert "post456" in result
        mock_create_collection_post.assert_called_once_with(
            collection_alias="myblog",
            body="Collection content",
            title="Collection Title",
            access_token="token123",
        )

    @pytest.mark.asyncio
    async def test_publish_post_to_collection_no_token(self, mock_get_access_token):
        """Test publishing to collection without token."""
        mock_get_access_token.return_value = None

        tool_func = get_tool_function(posts, "publish_post")

        result = await tool_func("Content", "Title", None, "myblog")
        assert "error" in result.lower()
        assert "authentication" in result.lower()

    @pytest.mark.asyncio
    async def test_publish_post_error(self, mock_get_access_token, mock_create_post):
        """Test publish post error handling."""
        mock_get_access_token.return_value = None
        mock_create_post.side_effect = WriteAsError("API Error")

        tool_func = get_tool_function(posts, "publish_post")

        result = await tool_func("Content", "Title")
        assert "failed" in result.lower()


class TestEditPost:
    """Tests for the edit_post tool."""

    @pytest.mark.asyncio
    async def test_edit_post_success(self, mock_get_access_token, mock_update_post):
        """Test successful post edit."""
        mock_get_access_token.return_value = "token123"
        mock_update_post.return_value = {
            "id": "post123",
            "slug": "updated-post",
            "body": "Updated content",
            "title": "Updated Title",
        }

        tool_func = get_tool_function(posts, "edit_post")

        result = await tool_func(
            "post123", "Updated content", "Updated Title", "token123"
        )
        assert "updated successfully" in result.lower()
        mock_update_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_edit_post_no_token(self, mock_get_access_token):
        """Test edit post without token."""
        mock_get_access_token.return_value = None

        tool_func = get_tool_function(posts, "edit_post")

        result = await tool_func("post123", "Content", None, "", None)
        assert "error" in result.lower()
        assert "required" in result.lower()

    @pytest.mark.asyncio
    async def test_edit_post_with_edit_token(
        self, mock_get_access_token, mock_update_post
    ):
        """Test edit post with edit token."""
        mock_get_access_token.return_value = None
        mock_update_post.return_value = {
            "id": "post123",
            "slug": "updated-post",
            "body": "Updated content",
        }

        tool_func = get_tool_function(posts, "edit_post")

        result = await tool_func(
            "post123", "Updated content", None, "", "edit_token_123"
        )
        assert "updated successfully" in result.lower()


class TestDeletePost:
    """Tests for the delete_post tool."""

    @pytest.mark.asyncio
    async def test_delete_post_success(self, mock_get_access_token, mock_delete_post):
        """Test successful post deletion."""
        mock_get_access_token.return_value = "token123"
        mock_delete_post.return_value = True

        tool_func = get_tool_function(posts, "delete_post")

        result = await tool_func("post123", "token123")
        assert "deleted successfully" in result.lower()
        mock_delete_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_post_no_token(self, mock_get_access_token):
        """Test delete post without token."""
        mock_get_access_token.return_value = None

        tool_func = get_tool_function(posts, "delete_post")

        result = await tool_func("post123", "", None)
        assert "error" in result.lower()

    @pytest.mark.asyncio
    async def test_delete_post_error(self, mock_get_access_token, mock_delete_post):
        """Test delete post error handling."""
        mock_get_access_token.return_value = "token123"
        mock_delete_post.side_effect = WriteAsError("Delete failed")

        tool_func = get_tool_function(posts, "delete_post")

        result = await tool_func("post123", "token123")
        assert "failed" in result.lower()


class TestReadPost:
    """Tests for the read_post tool."""

    @pytest.mark.asyncio
    async def test_read_post_success(self, mock_get_access_token, mock_get_post):
        """Test successful post read."""
        mock_get_access_token.return_value = None
        mock_get_post.return_value = {
            "id": "post123",
            "title": "Test Title",
            "body": "Test content",
            "views": 10,
        }

        tool_func = get_tool_function(posts, "read_post")

        result = await tool_func("post123")
        assert "Test Title" in result
        assert "Test content" in result
        assert "Views: 10" in result

    @pytest.mark.asyncio
    async def test_read_post_not_found(self, mock_get_access_token, mock_get_post):
        """Test reading non-existent post."""
        mock_get_access_token.return_value = None
        mock_get_post.return_value = {"error": "Post not found"}

        tool_func = get_tool_function(posts, "read_post")

        result = await tool_func("nonexistent")
        assert "not found" in result.lower()


class TestListMyPosts:
    """Tests for the list_my_posts tool."""

    @pytest.mark.asyncio
    async def test_list_my_posts_success(
        self, mock_get_access_token, mock_get_user_posts
    ):
        """Test successful listing of user posts."""
        mock_get_access_token.return_value = "token123"
        mock_get_user_posts.return_value = [
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

        tool_func = get_tool_function(posts, "list_my_posts")

        result = await tool_func("token123")
        assert "2 post(s)" in result
        assert "Post 1" in result
        assert "Post 2" in result

    @pytest.mark.asyncio
    async def test_list_my_posts_empty(
        self, mock_get_access_token, mock_get_user_posts
    ):
        """Test listing posts when user has none."""
        mock_get_access_token.return_value = "token123"
        mock_get_user_posts.return_value = []

        tool_func = get_tool_function(posts, "list_my_posts")

        result = await tool_func("token123")
        assert "no posts found" in result.lower()

    @pytest.mark.asyncio
    async def test_list_my_posts_no_token(self, mock_get_access_token):
        """Test listing posts without token."""
        mock_get_access_token.return_value = None

        tool_func = get_tool_function(posts, "list_my_posts")

        result = await tool_func("")
        assert "error" in result.lower()
        assert "required" in result.lower()
