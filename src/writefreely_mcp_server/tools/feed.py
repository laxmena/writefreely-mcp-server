"""
Public feed tools for WriteFreely MCP server.
"""

from ..api_client import get_read_writeas_posts, WriteAsError
from ..config import BASE_URL


def register_tools(mcp):
    """Register feed tools with the MCP server."""

    @mcp.tool()
    async def browse_public_feed(skip: int = 0) -> str:
        """
        Read posts from the public read.write.as feed.

        Args:
            skip: Number of posts to skip for pagination (default: 0, returns 10 posts per request)

        Returns:
            Formatted list of posts from the public feed
        """
        try:
            posts = await get_read_writeas_posts(skip=skip)

            if not posts:
                return "No posts found in the public feed."

            result = f"Public Feed (showing posts {skip + 1}-{skip + len(posts)}):\n\n"
            for i, post in enumerate(posts, 1):
                post_id = post.get("id", "unknown")
                slug = post.get("slug") or post_id
                title = post.get("title", "(no title)")
                created = post.get("created", "unknown date")
                views = post.get("views", 0)

                # Posts in read.write.as may have collection info
                collection = post.get("collection", {})
                collection_alias = collection.get("alias") if collection else None

                if collection_alias:
                    url = f"{BASE_URL}/{collection_alias}/{slug}"
                else:
                    url = f"{BASE_URL}/{slug}"

                result += f"{i}. {title}\n"
                result += f"   ID: {post_id}\n"
                result += f"   URL: {url}\n"
                if collection_alias:
                    result += f"   Collection: {collection_alias}\n"
                result += f"   Created: {created}\n"
                result += f"   Views: {views}\n\n"

            if len(posts) == 10:
                result += f"Note: There are more posts. Use skip={skip + 10} to see the next page."

            return result.strip()

        except WriteAsError as e:
            return f"Failed to browse public feed: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
