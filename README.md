# writefreely-mcp-server

An MCP server for WriteFreely that enables AI agents to publish and manage content on WriteFreely instances (including self-hosted instances and Write.as).

## Features

- Publish posts (anonymous or authenticated)
- Manage collections and posts
- Browse public feeds
- Support for Write.as and self-hosted WriteFreely instances

## Installation

### Using `uvx` (recommended)

```bash
uvx writefreely-mcp-server
```

### Using `uv`

```bash
uv tool install writefreely-mcp-server
writefreely-mcp
```

### Using `pip`

```bash
pip install writefreely-mcp-server
```

## Configuration

Configure via environment variables:

- `WRITEFREELY_BASE_URL` - Base URL (default: `https://write.as`)
- `WRITEFREELY_ACCESS_TOKEN` - Access token for authentication
- `WRITEFREELY_DEFAULT_LANGUAGE` - Default language (default: `en`)

### Getting an Access Token

```bash
curl -X POST https://write.as/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"alias": "your_username", "pass": "your_password"}'
```

### MCP Client Configuration

```json
{
  "mcpServers": {
    "writefreely": {
      "command": "uvx",
      "args": ["writefreely-mcp-server"],
      "env": {
        "WRITEFREELY_BASE_URL": "https://write.as",
        "WRITEFREELY_ACCESS_TOKEN": "your_token_here"
      }
    }
  }
}
```

## Available Tools

- `login()` - Authenticate with username/password
- `publish_post()` - Create and publish a new post
- `edit_post()` - Update an existing post
- `delete_post()` - Delete a post
- `read_post()` - Read a post by ID
- `list_my_posts()` - List all your posts
- `list_my_collections()` - List all your collections/blogs
- `browse_collection()` - Browse posts in a collection
- `update_collection()` - Update collection metadata
- `browse_public_feed()` - Browse the public feed

## License

MIT

## Links

- [Development](https://github.com/laxmena/writefreely-mcp-server/blob/main/DEVELOPMENT.md)
- [Contributing](https://github.com/laxmena/writefreely-mcp-server)
- [Issues](https://github.com/laxmena/writefreely-mcp-server/issues)
