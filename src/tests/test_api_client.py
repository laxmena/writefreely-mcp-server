"""
Tests for the WriteFreely API client.
"""

import pytest
import httpx
from unittest.mock import patch, AsyncMock, MagicMock

from writefreely_mcp_server.api_client import (
    authenticate,
    logout,
    create_post,
    get_post,
    update_post,
    delete_post,
    get_user_posts,
    create_collection,
    get_collection,
    update_collection,
    delete_collection,
    get_collection_post,
    create_collection_post,
    get_collection_posts,
    get_user_collections,
    get_user,
    get_user_channels,
    get_read_writeas_posts,
    render_markdown,
    WriteAsError,
    PostResponse,
    AuthResponse,
    UserResponse,
    CollectionResponse,
)


def create_mock_response(status_code, json_data=None, text=""):
    """Create a mock response with a request attached."""
    import json

    if json_data is not None:
        content = json.dumps(json_data).encode()
    else:
        content = text.encode() if text else b""
    response = httpx.Response(status_code, content=content)
    # Attach a mock request to allow raise_for_status() to work
    response._request = MagicMock()
    return response


@pytest.fixture
def mock_client():
    """Create a mock HTTP client with properly configured responses."""
    with patch("writefreely_mcp_server.api_client._get_client") as mock:
        client = AsyncMock()
        # Store the helper function on the client for tests to use
        client._create_mock_response = create_mock_response
        mock.return_value = client
        yield client


class TestAuthentication:
    """Tests for authentication functions."""

    @pytest.mark.asyncio
    async def test_authenticate_success(self, mock_client):
        """Test successful authentication."""
        mock_response = mock_client._create_mock_response(
            200,
            json_data={"data": {"access_token": "test_token_123"}},
        )
        mock_client.post.return_value = mock_response

        token = await authenticate("testuser", "testpass")
        assert token == "test_token_123"
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_failure(self, mock_client):
        """Test authentication failure returns empty string."""
        mock_response = mock_client._create_mock_response(
            401, json_data={"error": "Invalid credentials"}
        )
        mock_client.post.return_value = mock_response

        token = await authenticate("testuser", "wrongpass")
        assert token == ""

    @pytest.mark.asyncio
    async def test_logout_success(self, mock_client):
        """Test successful logout."""
        mock_response = mock_client._create_mock_response(204)
        mock_client.delete.return_value = mock_response

        result = await logout("test_token")
        assert result is True

    @pytest.mark.asyncio
    async def test_logout_failure(self, mock_client):
        """Test logout failure raises WriteAsError."""
        mock_response = mock_client._create_mock_response(
            401, json_data={"error": "Unauthorized"}
        )
        mock_client.delete.return_value = mock_response

        with pytest.raises(WriteAsError):
            await logout("invalid_token")


class TestPosts:
    """Tests for post management functions."""

    @pytest.mark.asyncio
    async def test_create_post_anonymous(self, mock_client):
        """Test creating an anonymous post."""
        mock_response = mock_client._create_mock_response(
            200,
            json_data={
                "data": {
                    "id": "post123",
                    "slug": "test-post",
                    "token": "edit_token_123",
                    "body": "Test content",
                    "title": "Test Title",
                    "created": "2024-01-01T00:00:00Z",
                    "views": 0,
                }
            },
        )
        mock_client.post.return_value = mock_response

        result = await create_post("Test content", "Test Title")
        assert result["id"] == "post123"
        assert result["slug"] == "test-post"
        assert result["token"] == "edit_token_123"

    @pytest.mark.asyncio
    async def test_create_post_authenticated(self, mock_client):
        """Test creating an authenticated post."""
        # Authenticated posts don't include edit tokens
        mock_response = mock_client._create_mock_response(
            200,
            json_data={
                "data": {
                    "id": "post456",
                    "slug": "auth-post",
                    "body": "Authenticated content",
                    "title": "Auth Title",
                    "created": "2024-01-01T00:00:00Z",
                    "views": 0,
                    # Note: no "token" field for authenticated posts
                }
            },
        )
        mock_client.post.return_value = mock_response

        result = await create_post("Authenticated content", "Auth Title", "token123")
        assert result["id"] == "post456"
        # Authenticated posts don't have edit tokens (token will be None if present)
        assert result.get("token") is None

    @pytest.mark.asyncio
    async def test_create_post_error(self, mock_client):
        """Test post creation error handling."""
        mock_response = mock_client._create_mock_response(
            400, json_data={"error": "Invalid request"}
        )
        mock_client.post.return_value = mock_response

        with pytest.raises(WriteAsError):
            await create_post("Content")

    @pytest.mark.asyncio
    async def test_get_post_success(self, mock_client):
        """Test retrieving a post."""
        mock_response = mock_client._create_mock_response(
            200,
            json_data={
                "data": {
                    "id": "post123",
                    "slug": "test-post",
                    "body": "Test content",
                    "title": "Test Title",
                    "created": "2024-01-01T00:00:00Z",
                    "views": 5,
                }
            },
        )
        mock_client.get.return_value = mock_response

        result = await get_post("post123")
        assert result["id"] == "post123"
        assert result["views"] == 5

    @pytest.mark.asyncio
    async def test_get_post_not_found(self, mock_client):
        """Test retrieving a non-existent post."""
        mock_response = mock_client._create_mock_response(
            404, json_data={"error": "Not found"}
        )
        mock_client.get.return_value = mock_response

        result = await get_post("nonexistent")
        assert "error" in result
        assert result["error"] == "Post not found"

    @pytest.mark.asyncio
    async def test_update_post_success(self, mock_client):
        """Test updating a post."""
        mock_response = mock_client._create_mock_response(
            200,
            json_data={
                "data": {
                    "id": "post123",
                    "slug": "test-post",
                    "body": "Updated content",
                    "title": "Updated Title",
                    "created": "2024-01-01T00:00:00Z",
                    "updated": "2024-01-02T00:00:00Z",
                    "views": 5,
                }
            },
        )
        mock_client.put.return_value = mock_response

        result = await update_post(
            "post123", "Updated content", "Updated Title", "token123"
        )
        assert result["body"] == "Updated content"
        assert result["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_delete_post_success(self, mock_client):
        """Test deleting a post."""
        mock_response = mock_client._create_mock_response(204)
        mock_client.delete.return_value = mock_response

        result = await delete_post("post123", access_token="token123")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_post_with_edit_token(self, mock_client):
        """Test deleting a post with edit token."""
        mock_response = mock_client._create_mock_response(204)
        mock_client.delete.return_value = mock_response

        result = await delete_post("post123", edit_token="edit_token_123")
        assert result is True

    @pytest.mark.asyncio
    async def test_get_user_posts(self, mock_client):
        """Test retrieving user's posts."""
        mock_response = mock_client._create_mock_response(
            200,
            json_data={
                "data": [
                    {
                        "id": "post1",
                        "slug": "post-1",
                        "title": "Post 1",
                        "body": "Content 1",
                        "created": "2024-01-01T00:00:00Z",
                        "views": 10,
                    },
                    {
                        "id": "post2",
                        "slug": "post-2",
                        "title": "Post 2",
                        "body": "Content 2",
                        "created": "2024-01-02T00:00:00Z",
                        "views": 20,
                    },
                ]
            },
        )
        mock_client.get.return_value = mock_response

        result = await get_user_posts("token123")
        assert len(result) == 2
        assert result[0]["id"] == "post1"
        assert result[1]["id"] == "post2"


class TestCollections:
    """Tests for collection management functions."""

    @pytest.mark.asyncio
    async def test_create_collection(self, mock_client):
        """Test creating a collection."""
        mock_response = mock_client._create_mock_response(
            200,
            json_data={
                "data": {
                    "alias": "myblog",
                    "title": "My Blog",
                    "description": "A test blog",
                    "views": 0,
                }
            },
        )
        mock_client.post.return_value = mock_response

        result = await create_collection("myblog", "My Blog", "token123", "A test blog")
        assert result["alias"] == "myblog"
        assert result["title"] == "My Blog"

    @pytest.mark.asyncio
    async def test_get_collection(self, mock_client):
        """Test retrieving a collection."""
        mock_response = mock_client._create_mock_response(
            200,
            json_data={
                "data": {
                    "alias": "myblog",
                    "title": "My Blog",
                    "description": "A test blog",
                    "views": 100,
                }
            },
        )
        mock_client.get.return_value = mock_response

        result = await get_collection("myblog")
        assert result["alias"] == "myblog"
        assert result["views"] == 100

    @pytest.mark.asyncio
    async def test_get_collection_not_found(self, mock_client):
        """Test retrieving a non-existent collection."""
        mock_response = mock_client._create_mock_response(
            404, json_data={"error": "Not found"}
        )
        mock_client.get.return_value = mock_response

        result = await get_collection("nonexistent")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_update_collection(self, mock_client):
        """Test updating a collection."""
        mock_response = mock_client._create_mock_response(
            200,
            json_data={
                "data": {
                    "alias": "myblog",
                    "title": "Updated Blog",
                    "description": "Updated description",
                    "views": 100,
                }
            },
        )
        mock_client.put.return_value = mock_response

        result = await update_collection(
            "myblog", "token123", "Updated Blog", "Updated description"
        )
        assert result["title"] == "Updated Blog"

    @pytest.mark.asyncio
    async def test_delete_collection(self, mock_client):
        """Test deleting a collection."""
        mock_response = mock_client._create_mock_response(204)
        mock_client.delete.return_value = mock_response

        result = await delete_collection("myblog", "token123")
        assert result is True

    @pytest.mark.asyncio
    async def test_create_collection_post(self, mock_client):
        """Test creating a post in a collection."""
        mock_response = mock_client._create_mock_response(
            200,
            json_data={
                "data": {
                    "id": "post789",
                    "slug": "collection-post",
                    "body": "Collection post content",
                    "title": "Collection Post",
                    "created": "2024-01-01T00:00:00Z",
                    "views": 0,
                }
            },
        )
        mock_client.post.return_value = mock_response

        result = await create_collection_post(
            "myblog", "Collection post content", "Collection Post", "token123"
        )
        assert result["id"] == "post789"
        assert result["slug"] == "collection-post"

    @pytest.mark.asyncio
    async def test_get_collection_posts(self, mock_client):
        """Test retrieving posts from a collection."""
        mock_response = mock_client._create_mock_response(
            200,
            json_data={
                "data": [
                    {
                        "id": "post1",
                        "slug": "post-1",
                        "title": "Post 1",
                        "body": "Content 1",
                        "created": "2024-01-01T00:00:00Z",
                        "views": 10,
                    }
                ]
            },
        )
        mock_client.get.return_value = mock_response

        result = await get_collection_posts("myblog", page=1)
        assert len(result) == 1
        assert result[0]["id"] == "post1"

    @pytest.mark.asyncio
    async def test_get_user_collections(self, mock_client):
        """Test retrieving user's collections."""
        mock_response = mock_client._create_mock_response(
            200,
            json_data={
                "data": [
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
            },
        )
        mock_client.get.return_value = mock_response

        result = await get_user_collections("token123")
        assert len(result) == 2
        assert result[0]["alias"] == "blog1"
        assert result[1]["alias"] == "blog2"


class TestUser:
    """Tests for user-related functions."""

    @pytest.mark.asyncio
    async def test_get_user(self, mock_client):
        """Test retrieving user information."""
        mock_response = mock_client._create_mock_response(
            200,
            json_data={
                "data": {
                    "id": "user123",
                    "username": "testuser",
                    "email": "test@example.com",
                }
            },
        )
        mock_client.get.return_value = mock_response

        result = await get_user("token123")
        assert result["id"] == "user123"
        assert result["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_get_user_channels(self, mock_client):
        """Test retrieving user channels."""
        mock_response = mock_client._create_mock_response(
            200,
            json_data={
                "data": [
                    {"id": "channel1", "name": "Tumblr", "method": "tumblr"},
                    {"id": "channel2", "name": "Medium", "method": "medium"},
                ]
            },
        )
        mock_client.get.return_value = mock_response

        result = await get_user_channels("token123")
        assert len(result) == 2
        assert result[0]["method"] == "tumblr"


class TestFeed:
    """Tests for feed functions."""

    @pytest.mark.asyncio
    async def test_get_read_writeas_posts(self, mock_client):
        """Test retrieving posts from read.write.as."""
        mock_response = mock_client._create_mock_response(
            200,
            json_data={
                "data": [
                    {
                        "id": "feed1",
                        "slug": "feed-post-1",
                        "title": "Feed Post 1",
                        "body": "Feed content",
                        "created": "2024-01-01T00:00:00Z",
                        "views": 100,
                    }
                ]
            },
        )
        mock_client.get.return_value = mock_response

        result = await get_read_writeas_posts(skip=0)
        assert len(result) == 1
        assert result[0]["id"] == "feed1"

    @pytest.mark.asyncio
    async def test_get_read_writeas_posts_pagination(self, mock_client):
        """Test pagination for read.write.as posts."""
        mock_response = mock_client._create_mock_response(
            200,
            json_data={"data": []},
        )
        mock_client.get.return_value = mock_response

        result = await get_read_writeas_posts(skip=10)
        assert len(result) == 0
        # Verify skip parameter was used
        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["skip"] == 10


class TestMarkdown:
    """Tests for markdown rendering."""

    @pytest.mark.asyncio
    async def test_render_markdown(self, mock_client):
        """Test rendering markdown to HTML."""
        mock_response = mock_client._create_mock_response(
            200,
            json_data={"data": {"html": "<p>Test content</p>"}},
        )
        mock_client.post.return_value = mock_response

        result = await render_markdown("Test content")
        assert result == "<p>Test content</p>"

    @pytest.mark.asyncio
    async def test_render_markdown_error(self, mock_client):
        """Test markdown rendering error handling."""
        mock_response = mock_client._create_mock_response(
            400, json_data={"error": "Invalid markdown"}
        )
        mock_client.post.return_value = mock_response

        with pytest.raises(WriteAsError):
            await render_markdown("Invalid content")
