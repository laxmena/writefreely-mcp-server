"""
Collection/blog management tools for WriteFreely MCP server.
"""


from ..api_client import (
    WriteAsError,
    get_collection_posts,
    get_user_collections,
)
from ..config import BASE_URL, get_access_token


def register_tools(mcp):
    """Register collection management tools with the MCP server."""

    @mcp.tool()
    async def list_my_collections(access_token: str | None = None) -> str:
        """
        Get all blogs/collections owned by the authenticated user.

        Args:
            access_token: Access token from login() or WRITEFREELY_ACCESS_TOKEN env var
                         (optional if token is set via env var)

        Returns:
            Formatted list of all user's collections with aliases, titles, and URLs
        """
        try:
            # Get token from parameter or environment variable
            token = get_access_token(access_token)

            if not token:
                return (
                    "Error: Access token is required. Provide access_token "
                    "parameter or set WRITEFREELY_ACCESS_TOKEN environment variable."
                )

            collections = await get_user_collections(token)

            if not collections:
                return "No collections found for this user."

            result = f"Found {len(collections)} collection(s):\n\n"
            for i, collection in enumerate(collections, 1):
                alias = collection.get("alias", "unknown")
                title = collection.get("title", "(no title)")
                description = collection.get("description", "")
                views = collection.get("views", 0)
                url = f"{BASE_URL}/api/collections/{alias}/posts"

                result += f"{i}. {title}\n"
                result += f"   Alias: {alias}\n"
                result += f"   URL: {url}\n"
                if description:
                    result += f"   Description: {description}\n"
                result += f"   Views: {views}\n\n"

            return result.strip()

        except WriteAsError as e:
            return f"Failed to list collections: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"

    @mcp.tool()
    async def browse_collection(
        collection_alias: str,
        page: int = 1,
    ) -> str:
        """
        List posts in a specific collection/blog.

        Args:
            collection_alias: The alias/name of the collection to browse
            page: Page number for pagination (default: 1, returns 10 posts per page)

        Returns:
            Formatted list of posts in the collection
        """
        try:
            posts = await get_collection_posts(collection_alias, page=page)

            if not posts:
                return (
                    f"No posts found in collection '{collection_alias}' (page {page})."
                )

            result = (
                f"Collection '{collection_alias}' - Page {page} "
                f"({len(posts)} post(s)):\n\n"
            )
            for i, post in enumerate(posts, 1):
                post_id = post.get("id", "unknown")
                slug = post.get("slug") or post_id
                title = post.get("title", "(no title)")
                created = post.get("created", "unknown date")
                views = post.get("views", 0)
                url = f"{BASE_URL}/{collection_alias}/{slug}"

                result += f"{i}. {title}\n"
                result += f"   ID: {post_id}\n"
                result += f"   URL: {url}\n"
                result += f"   Created: {created}\n"
                result += f"   Views: {views}\n\n"

            if len(posts) == 10:
                result += (
                    f"Note: There may be more posts. Try page {page + 1} for more."
                )

            return result.strip()

        except WriteAsError as e:
            return f"Failed to browse collection: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
