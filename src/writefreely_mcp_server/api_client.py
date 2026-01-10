"""
Low-level async HTTP client for WriteFreely API.
Implements all methods from writeasapi library using httpx for native async support.
API Docs: https://developers.write.as/docs/api/

Note: Per WriteFreely API guidelines, this library uses "WriteFreely" branding
to support both self-hosted WriteFreely instances and the Write.as hosted service.
"""

import asyncio
import logging
import httpx
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, ValidationError

from .config import BASE_URL, READ_WRITEAS_URL, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

# Shared HTTP client instance for connection pooling and efficiency
_client: Optional[httpx.AsyncClient] = None
_client_lock = asyncio.Lock()


class WriteAsError(Exception):
    """Base exception for WriteFreely API errors."""

    pass


class PostResponse(BaseModel):
    """Post response model."""

    id: str
    slug: Optional[str] = None
    token: Optional[str] = None  # edit/delete token for anonymous posts
    body: str
    title: Optional[str] = None
    created: str
    updated: Optional[str] = None
    views: int = 0


class AuthResponse(BaseModel):
    """Response from /api/auth/login"""

    access_token: str


class UserResponse(BaseModel):
    """User information response."""

    id: str
    username: str
    email: Optional[str] = None


class CollectionResponse(BaseModel):
    """Collection/blog response model."""

    alias: str
    title: str
    description: Optional[str] = None
    style_sheet: Optional[str] = None
    views: int = 0


class ChannelResponse(BaseModel):
    """Channel response model (Tumblr, Medium, etc.)."""

    id: str
    name: str
    method: str  # e.g., "tumblr", "medium"


def _get_headers(access_token: Optional[str] = None) -> Dict[str, str]:
    """Get request headers with optional authorization."""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if access_token:
        headers["Authorization"] = f"{access_token}"
    return headers


def _parse_response(
    model_class: Type[BaseModel], data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Parse response data using Pydantic model, falling back to raw data on validation error.

    Args:
        model_class: Pydantic model class to validate against
        data: Raw response data dictionary

    Returns:
        Validated model as dict, or raw data if validation fails
    """
    try:
        return model_class(**data).model_dump()
    except ValidationError:
        return data


async def _get_client() -> httpx.AsyncClient:
    """Get or create the shared HTTP client instance (thread-safe)."""
    global _client
    if _client is None:
        async with _client_lock:
            if _client is None:
                _client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT)
    return _client


# ============================================================================
# Authentication
# ============================================================================


async def authenticate(username: str, password: str, base_url: str = BASE_URL) -> str:
    """
    Authenticate user and return access token.
    Returns empty string on failure (no exception raised - for tool friendliness).
    """
    url = f"{base_url}/api/auth/login"
    payload = {"alias": username, "pass": password}

    client = await _get_client()
    try:
        logger.debug(f"Authenticating with WriteFreely API at {url}")
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        auth = AuthResponse(**data.get("data", {}))
        logger.debug("Authentication successful, token obtained")
        return auth.access_token
    except httpx.HTTPStatusError as e:
        logger.warning(
            f"Authentication failed: HTTP {e.response.status_code} - {e.response.text}"
        )
        return ""
    except (ValidationError, KeyError) as e:
        logger.error(f"Authentication failed: Invalid response format - {e}")
        return ""


async def logout(access_token: str, base_url: str = BASE_URL) -> bool:
    """
    Log out user and invalidate access token.
    Returns True on success.
    """
    url = f"{base_url}/api/auth/me"
    headers = _get_headers(access_token)

    client = await _get_client()
    try:
        resp = await client.delete(url, headers=headers)
        resp.raise_for_status()
        # Successful logout returns 204 with no content
        return True
    except httpx.HTTPStatusError as e:
        raise WriteAsError(
            f"Logout failed: {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        raise WriteAsError(f"Logout failed: {str(e)}")


# ============================================================================
# Posts
# ============================================================================


async def create_post(
    body: str,
    title: Optional[str] = None,
    access_token: Optional[str] = None,
    created: Optional[str] = None,  # ISO 8601 format
    base_url: str = BASE_URL,
) -> Dict[str, Any]:
    """
    Create a new post (anonymous or authenticated, but NOT in a blog collection).
    - With access_token → authenticated post
    - Without token → anonymous post (returns edit token), will be deleted in few hours automatically
    - created: Optional ISO 8601 datetime string for backdating posts

    For posting to a collection, use create_collection_post() instead.
    """
    url = f"{base_url}/api/posts"

    payload: Dict[str, Any] = {
        "body": body,
        "title": title or "",
    }

    if created:
        payload["created"] = created

    headers = _get_headers(access_token)
    is_authenticated = bool(access_token)

    client = await _get_client()
    try:
        logger.debug(
            f"Creating {'authenticated' if is_authenticated else 'anonymous'} post at {url}"
        )
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json().get("data", {})

        # Try to parse as structured post
        result = _parse_response(PostResponse, data)
        if "id" in result:
            logger.info(f"Post created successfully: {result['id']}")
        else:
            logger.debug("Post created but response validation failed, using raw data")
        return result

    except httpx.HTTPStatusError as e:
        logger.error(
            f"Failed to create post: HTTP {e.response.status_code} - {e.response.text}"
        )
        raise WriteAsError(
            f"Failed to create post: {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating post: {str(e)}")
        raise WriteAsError(f"Unexpected error creating post: {str(e)}")


async def get_post(
    post_id: str, access_token: Optional[str] = None, base_url: str = BASE_URL
) -> Dict[str, Any]:
    """Retrieve a single post by ID."""
    url = f"{base_url}/api/posts/{post_id}"
    headers = _get_headers(access_token)

    client = await _get_client()
    try:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json().get("data", {})

        # Try to validate with Pydantic
        return _parse_response(PostResponse, data)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"error": "Post not found"}
        raise WriteAsError(f"Failed to get post: {e.response.status_code}")
    except Exception as e:
        raise WriteAsError(f"Failed to get post: {str(e)}")


async def update_post(
    post_id: str,
    body: str,
    title: Optional[str] = None,
    access_token: Optional[str] = None,
    edit_token: Optional[str] = None,
    base_url: str = BASE_URL,
) -> Dict[str, Any]:
    """Update existing post (requires access_token or edit_token)."""
    url = f"{base_url}/api/posts/{post_id}"

    payload = {"body": body}
    if title is not None:
        payload["title"] = title

    token = edit_token or access_token
    headers = _get_headers(token) if token else {}

    client = await _get_client()
    try:
        logger.debug(f"Updating post {post_id} at {url}")
        resp = await client.put(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json().get("data", {})

        # Try to validate with Pydantic
        result = _parse_response(PostResponse, data)
        if "id" in result:
            logger.info(f"Post {post_id} updated successfully")
        else:
            logger.debug(
                f"Post {post_id} updated but response validation failed, using raw data"
            )
        return result

    except httpx.HTTPStatusError as e:
        logger.error(
            f"Failed to update post {post_id}: HTTP {e.response.status_code} - {e.response.text}"
        )
        raise WriteAsError(
            f"Update failed: {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Unexpected error updating post {post_id}: {str(e)}")
        raise WriteAsError(f"Update failed: {str(e)}")


async def delete_post(
    post_id: str,
    access_token: Optional[str] = None,
    edit_token: Optional[str] = None,
    base_url: str = BASE_URL,
) -> bool:
    """
    Delete a post permanently.
    Requires either access_token (for authenticated posts) or edit_token (for anonymous posts).
    """
    url = f"{base_url}/api/posts/{post_id}"

    # Use edit_token if provided, otherwise use access_token
    token = edit_token or access_token
    headers = _get_headers(token) if token else {}

    client = await _get_client()
    try:
        logger.debug(f"Deleting post {post_id} at {url}")
        resp = await client.delete(url, headers=headers)
        resp.raise_for_status()
        logger.info(f"Post {post_id} deleted successfully")
        return True
    except httpx.HTTPStatusError as e:
        logger.error(
            f"Failed to delete post {post_id}: HTTP {e.response.status_code} - {e.response.text}"
        )
        raise WriteAsError(
            f"Delete failed: {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting post {post_id}: {str(e)}")
        raise WriteAsError(f"Delete failed: {str(e)}")


async def get_user_posts(
    access_token: str, base_url: str = BASE_URL
) -> List[Dict[str, Any]]:
    """Retrieve all posts for the authenticated user."""
    url = f"{base_url}/api/me/posts"
    headers = _get_headers(access_token)

    client = await _get_client()
    try:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        return data if isinstance(data, list) else []
    except httpx.HTTPStatusError as e:
        raise WriteAsError(f"Failed to get user posts: {e.response.status_code}")
    except Exception as e:
        raise WriteAsError(f"Failed to get user posts: {str(e)}")


# ============================================================================
# Collections (Blogs)
# ============================================================================


async def create_collection(
    alias: str,
    title: str,
    access_token: str,
    description: Optional[str] = None,
    base_url: str = BASE_URL,
) -> Dict[str, Any]:
    """Create a new collection (blog)."""
    url = f"{base_url}/api/collections"

    payload: Dict[str, Any] = {
        "alias": alias,
        "title": title,
    }
    if description:
        payload["description"] = description

    headers = _get_headers(access_token)

    client = await _get_client()
    try:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json().get("data", {})

        # Try to validate with Pydantic
        return _parse_response(CollectionResponse, data)

    except httpx.HTTPStatusError as e:
        raise WriteAsError(
            f"Failed to create collection: {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        raise WriteAsError(f"Failed to create collection: {str(e)}")


async def get_collection(alias: str, base_url: str = BASE_URL) -> Dict[str, Any]:
    """Retrieve a collection by alias."""
    url = f"{base_url}/api/collections/{alias}"

    client = await _get_client()
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json().get("data", {})

        # Try to validate with Pydantic
        return _parse_response(CollectionResponse, data)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"error": "Collection not found"}
        raise WriteAsError(f"Failed to get collection: {e.response.status_code}")
    except Exception as e:
        raise WriteAsError(f"Failed to get collection: {str(e)}")


async def update_collection(
    alias: str,
    access_token: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    style_sheet: Optional[str] = None,
    base_url: str = BASE_URL,
) -> Dict[str, Any]:
    """Update a collection."""
    url = f"{base_url}/api/collections/{alias}"

    payload: Dict[str, Any] = {}
    if title is not None:
        payload["title"] = title
    if description is not None:
        payload["description"] = description
    if style_sheet is not None:
        payload["style_sheet"] = style_sheet

    headers = _get_headers(access_token)

    client = await _get_client()
    try:
        resp = await client.put(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json().get("data", {})

        # Try to validate with Pydantic
        return _parse_response(CollectionResponse, data)

    except httpx.HTTPStatusError as e:
        raise WriteAsError(
            f"Failed to update collection: {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        raise WriteAsError(f"Failed to update collection: {str(e)}")


async def delete_collection(
    alias: str, access_token: str, base_url: str = BASE_URL
) -> bool:
    """Delete a collection."""
    url = f"{base_url}/api/collections/{alias}"
    headers = _get_headers(access_token)

    client = await _get_client()
    try:
        resp = await client.delete(url, headers=headers)
        resp.raise_for_status()
        return True
    except httpx.HTTPStatusError as e:
        raise WriteAsError(
            f"Delete collection failed: {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        raise WriteAsError(f"Delete collection failed: {str(e)}")


async def get_collection_post(
    collection_alias: str, post_slug: str, base_url: str = BASE_URL
) -> Dict[str, Any]:
    """Retrieve a specific post from a collection by slug."""
    url = f"{base_url}/api/collections/{collection_alias}/posts/{post_slug}"

    client = await _get_client()
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json().get("data", {})

        # Try to validate with Pydantic
        return _parse_response(PostResponse, data)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"error": "Post not found"}
        raise WriteAsError(f"Failed to get collection post: {e.response.status_code}")
    except Exception as e:
        raise WriteAsError(f"Failed to get collection post: {str(e)}")


async def create_collection_post(
    collection_alias: str,
    body: str,
    title: Optional[str] = None,
    access_token: str = "",
    created: Optional[str] = None,  # ISO 8601 format
    base_url: str = BASE_URL,
) -> Dict[str, Any]:
    """
    Publish a new post to a collection (blog).
    Requires authentication (access_token).
    - created: Optional ISO 8601 datetime string for backdating posts

    This uses the endpoint: POST /api/collections/{alias}/posts
    """
    url = f"{base_url}/api/collections/{collection_alias}/posts"

    payload: Dict[str, Any] = {
        "body": body,
        "title": title or "",
    }

    if created:
        payload["created"] = created

    headers = _get_headers(access_token) if access_token else {}

    client = await _get_client()
    try:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json().get("data", {})

        # Try to parse as structured post
        return _parse_response(PostResponse, data)

    except httpx.HTTPStatusError as e:
        raise WriteAsError(
            f"Failed to create collection post: {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        raise WriteAsError(f"Unexpected error creating collection post: {str(e)}")


async def get_collection_posts(
    collection_alias: str, page: int = 1, base_url: str = BASE_URL
) -> List[Dict[str, Any]]:
    """
    Retrieve posts from a collection.
    Returns up to 10 posts per page. Use page parameter for pagination.
    """
    url = f"{base_url}/api/collections/{collection_alias}/posts"

    params = {}
    if page > 1:
        params["page"] = page

    client = await _get_client()
    try:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        return data if isinstance(data, list) else []
    except httpx.HTTPStatusError as e:
        raise WriteAsError(f"Failed to get collection posts: {e.response.status_code}")
    except Exception as e:
        raise WriteAsError(f"Failed to get collection posts: {str(e)}")


async def move_post_to_collection(
    post_id: str, collection_alias: str, access_token: str, base_url: str = BASE_URL
) -> Dict[str, Any]:
    """Move a post to a collection."""
    url = f"{base_url}/api/collections/{collection_alias}/posts/{post_id}"
    headers = _get_headers(access_token)

    client = await _get_client()
    try:
        resp = await client.put(url, headers=headers)
        resp.raise_for_status()
        data = resp.json().get("data", {})

        # Try to validate with Pydantic
        return _parse_response(PostResponse, data)

    except httpx.HTTPStatusError as e:
        raise WriteAsError(
            f"Failed to move post to collection: {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        raise WriteAsError(f"Failed to move post to collection: {str(e)}")


async def pin_post_to_collection(
    post_id: str, collection_alias: str, access_token: str, base_url: str = BASE_URL
) -> bool:
    """Pin a post to the top of a collection."""
    url = f"{base_url}/api/collections/{collection_alias}/posts/{post_id}/pin"
    headers = _get_headers(access_token)

    client = await _get_client()
    try:
        resp = await client.post(url, headers=headers)
        resp.raise_for_status()
        return True
    except httpx.HTTPStatusError as e:
        raise WriteAsError(
            f"Failed to pin post: {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        raise WriteAsError(f"Failed to pin post: {str(e)}")


async def unpin_post_from_collection(
    post_id: str, collection_alias: str, access_token: str, base_url: str = BASE_URL
) -> bool:
    """Unpin a post from a collection."""
    url = f"{base_url}/api/collections/{collection_alias}/posts/{post_id}/pin"
    headers = _get_headers(access_token)

    client = await _get_client()
    try:
        resp = await client.delete(url, headers=headers)
        resp.raise_for_status()
        return True
    except httpx.HTTPStatusError as e:
        raise WriteAsError(
            f"Failed to unpin post: {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        raise WriteAsError(f"Failed to unpin post: {str(e)}")


async def get_user_collections(
    access_token: str, base_url: str = BASE_URL
) -> List[Dict[str, Any]]:
    """Retrieve all collections for the authenticated user."""
    url = f"{base_url}/api/me/collections"
    headers = _get_headers(access_token)

    client = await _get_client()
    try:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        return data if isinstance(data, list) else []
    except httpx.HTTPStatusError as e:
        raise WriteAsError(
            f"Failed to get user collections: {e.response.status_code}, url: {url}, access_token: {access_token}"
        )
    except Exception as e:
        raise WriteAsError(
            f"Failed to get user collections: {str(e)}, url: {url}, access_token: {access_token}"
        )


# ============================================================================
# User
# ============================================================================


async def get_user(access_token: str, base_url: str = BASE_URL) -> Dict[str, Any]:
    """Retrieve authenticated user information."""
    url = f"{base_url}/api/me"
    headers = _get_headers(access_token)

    client = await _get_client()
    try:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json().get("data", {})

        # Try to validate with Pydantic
        return _parse_response(UserResponse, data)

    except httpx.HTTPStatusError as e:
        raise WriteAsError(f"Failed to get user: {e.response.status_code}")
    except Exception as e:
        raise WriteAsError(f"Failed to get user: {str(e)}")


async def get_user_channels(
    access_token: str, base_url: str = BASE_URL
) -> List[Dict[str, Any]]:
    """Retrieve channels (Tumblr, Medium, etc.) for the authenticated user."""
    url = f"{base_url}/api/me/channels"
    headers = _get_headers(access_token)

    client = await _get_client()
    try:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        return data if isinstance(data, list) else []
    except httpx.HTTPStatusError as e:
        raise WriteAsError(f"Failed to get user channels: {e.response.status_code}")
    except Exception as e:
        raise WriteAsError(f"Failed to get user channels: {str(e)}")


# ============================================================================
# Read.write.as
# ============================================================================


async def get_read_writeas_posts(
    skip: int = 0, base_url: str = READ_WRITEAS_URL
) -> List[Dict[str, Any]]:
    """
    Retrieve posts from read.write.as (public writing feed).
    skip: Number of posts to skip (for pagination).
    Returns 10 posts per request.
    """
    url = f"{base_url}/api/read"

    params = {}
    if skip > 0:
        params["skip"] = skip

    client = await _get_client()
    try:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        return data if isinstance(data, list) else []
    except httpx.HTTPStatusError as e:
        raise WriteAsError(f"Failed to get {base_url} posts: {e.response.status_code}")
    except Exception as e:
        raise WriteAsError(f"Failed to get {base_url} posts: {str(e)}")


# ============================================================================
# Markdown
# ============================================================================


async def render_markdown(markdown: str, base_url: str = BASE_URL) -> str:
    """Render Markdown to HTML using WriteFreely API."""
    url = f"{base_url}/api/markdown"
    payload = {"md": markdown}

    client = await _get_client()
    try:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        # The API returns HTML in the response
        return data.get("data", {}).get("html", markdown)
    except httpx.HTTPStatusError as e:
        raise WriteAsError(
            f"Failed to render markdown: {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        raise WriteAsError(f"Failed to render markdown: {str(e)}")
