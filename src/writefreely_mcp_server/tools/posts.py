"""
Post management tools for WriteFreely MCP server.
"""

import logging
from typing import Optional

from ..api_client import (
    create_post,
    create_collection_post,
    get_post,
    update_post,
    delete_post as api_delete_post,
    get_user_posts,
    WriteAsError,
)
from ..config import BASE_URL, get_access_token

logger = logging.getLogger(__name__)


def register_tools(mcp):
    """Register post management tools with the MCP server."""

    @mcp.tool()
    async def publish_post(
        content: str,
        title: Optional[str] = None,
        access_token: Optional[str] = None,
        collection: Optional[str] = None,
    ) -> str:
        """
        Create and publish a new post on WriteFreely.
        Supports anonymous posts or publishing to a specific collection/blog.

        Args:
            content:     The main body of the post (Markdown supported)
            title:       Optional post title
            access_token: Access token from login() or WRITEFREELY_ACCESS_TOKEN env var
                         Leave empty for anonymous publishing or to use env var token
            collection:  Optional blog/collection alias to publish into
                         (only works with access_token)

        Returns:
            Success message with post URL or error
        """
        try:
            # Get token from parameter or environment variable
            token = (
                get_access_token(access_token) if access_token else get_access_token()
            )
            logger.debug(
                f"Publishing post - collection: {collection}, has_token: {bool(token)}"
            )

            # Use collection-specific endpoint if collection is provided
            if collection:
                if not token:
                    logger.warning(
                        f"Attempted to publish to collection {collection} without authentication"
                    )
                    return "Error: Publishing to a collection requires authentication. Please provide an access_token or set WRITEFREELY_ACCESS_TOKEN environment variable."
                result = await create_collection_post(
                    collection_alias=collection,
                    body=content,
                    title=title,
                    access_token=token,
                )
            else:
                result = await create_post(
                    body=content,
                    title=title,
                    access_token=token,
                )

            post_id = result.get("id", "unknown")
            slug_or_id = result.get("slug") or post_id

            # For anonymous posts you get an edit token
            edit_token = result.get("token")

            url = f"{BASE_URL}/{slug_or_id}"

            msg = f"Post created successfully!\nURL: {url}\nID: {post_id}"

            if edit_token:
                msg += f"\nEdit/Delete token (save it!): {edit_token}"
            if token:
                msg += "\nPublished as authenticated user."

            return msg

        except WriteAsError as e:
            return f"Failed to publish post: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def edit_post(
        post_id: str,
        content: str,
        title: Optional[str] = None,
        access_token: str = "",
        edit_token: Optional[str] = None,
    ) -> str:
        """
        Update an existing post's content and/or title.

        Args:
            post_id: The ID of the post to update
            content: The new body content for the post (Markdown supported)
            title: Optional new title (leave None to keep existing title)
            access_token: Access token from login() or WRITEFREELY_ACCESS_TOKEN env var
                         (optional if token is set via env var)
            edit_token: Edit token for anonymous posts (from publish_post response)

        Returns:
            Success message with updated post URL or error
        """
        try:
            # Get token from parameter or environment variable
            token = get_access_token(access_token)
            logger.debug(
                f"Editing post {post_id} - has_token: {bool(token)}, has_edit_token: {bool(edit_token)}"
            )

            if not token and not edit_token:
                logger.warning(f"Attempted to edit post {post_id} without token")
                return "Error: Either access_token (for authenticated posts) or edit_token (for anonymous posts) is required. You can also set WRITEFREELY_ACCESS_TOKEN environment variable."

            result = await update_post(
                post_id=post_id,
                body=content,
                title=title,
                access_token=token if token else "",
            )

            post_id_updated = result.get("id", post_id)
            slug_or_id = result.get("slug") or post_id_updated
            url = f"{BASE_URL}/{slug_or_id}"

            return f"Post updated successfully!\nURL: {url}\nID: {post_id_updated}"

        except WriteAsError as e:
            return f"Failed to edit post: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def delete_post(
        post_id: str,
        access_token: str = "",
        edit_token: Optional[str] = None,
    ) -> str:
        """
        Permanently delete a post.

        Args:
            post_id: The ID of the post to delete
            access_token: Access token from login() or WRITEFREELY_ACCESS_TOKEN env var
                         (optional if token is set via env var)
            edit_token: Edit token for anonymous posts (from publish_post response)

        Returns:
            Success or error message
        """
        try:
            # Get token from parameter or environment variable
            token = get_access_token(access_token)
            logger.debug(
                f"Deleting post {post_id} - has_token: {bool(token)}, has_edit_token: {bool(edit_token)}"
            )

            if not token and not edit_token:
                logger.warning(f"Attempted to delete post {post_id} without token")
                return "Error: Either access_token (for authenticated posts) or edit_token (for anonymous posts) is required. You can also set WRITEFREELY_ACCESS_TOKEN environment variable."

            success = await api_delete_post(
                post_id=post_id,
                access_token=token,
                edit_token=edit_token,
            )

            if success:
                return f"Post {post_id} deleted successfully."
            else:
                return f"Failed to delete post {post_id}."

        except WriteAsError as e:
            return f"Failed to delete post: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def read_post(post_id: str, access_token: Optional[str] = None) -> str:
        """
        Retrieve the content of an existing post by its ID.

        Args:
            post_id: The ID of the post (or slug for public posts)
            access_token: Optional - needed only for private/draft posts
                         Can also use WRITEFREELY_ACCESS_TOKEN env var

        Returns:
            Post title + body (or error message)
        """
        try:
            # Get token from parameter or environment variable
            token = get_access_token(access_token)
            data = await get_post(post_id, token)

            if "error" in data:
                return data["error"]

            title = data.get("title", "(no title)")
            body = data.get("body", "(empty)")
            views = data.get("views", 0)

            return f"Title: {title}\n\n{body}\n\nViews: {views}"
        except WriteAsError as e:
            return f"Could not read post: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def list_my_posts(access_token: str = "") -> str:
        """
        Retrieve all posts for the authenticated user.

        Args:
            access_token: Access token from login() or WRITEFREELY_ACCESS_TOKEN env var
                         (optional if token is set via env var)

        Returns:
            Formatted list of all user's posts with IDs, titles, and URLs
        """
        try:
            # Get token from parameter or environment variable
            token = get_access_token(access_token)
            logger.debug(f"Listing user posts - has_token: {bool(token)}")

            if not token:
                logger.warning("Attempted to list user posts without authentication")
                return "Error: Access token is required. Provide access_token parameter or set WRITEFREELY_ACCESS_TOKEN environment variable."

            posts = await get_user_posts(token)

            if not posts:
                return "No posts found for this user."

            result = f"Found {len(posts)} post(s):\n\n"
            for i, post in enumerate(posts, 1):
                post_id = post.get("id", "unknown")
                slug = post.get("slug") or post_id
                title = post.get("title", "(no title)")
                created = post.get("created", "unknown date")
                views = post.get("views", 0)
                url = f"{BASE_URL}/{slug}"

                result += f"{i}. {title}\n"
                result += f"   ID: {post_id}\n"
                result += f"   URL: {url}\n"
                result += f"   Created: {created}\n"
                result += f"   Views: {views}\n\n"

            return result.strip()

        except WriteAsError as e:
            return f"Failed to list posts: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
