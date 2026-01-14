# writefreely-mcp-server

<p align="center">
<a href="https://github.com/laxmena/writefreely-mcp-server"><img alt="Source Code" src="https://img.shields.io/badge/source-code-blue"/></a>
<a href="https://github.com/laxmena/writefreely-mcp-server"><img alt="Issues" src="https://img.shields.io/badge/issue-tracker-blue"/></a>
<img alt="Python 3.10 | 3.11 | 3.12 " src="https://img.shields.io/pypi/pyversions/writefreely-mcp-server"/>
<a href="https://pypi.org/project/writefreely-mcp-server/"><img alt="PyPI" src="https://img.shields.io/pypi/v/writefreely-mcp-server"/></a>
<a href="https://github.com/laxmena/writefreely-mcp-server/tree/main/LICENSE"><img alt="MIT License" src="https://img.shields.io/pypi/l/writefreely-mcp-server"/></a>
</p>


An MCP server for WriteFreely that enables AI agents to publish and manage content on WriteFreely instances (including self-hosted instances and Write.as).

## Features

- Publish posts (anonymous or authenticated)
- Manage collections and posts
- Browse public feeds
- Support for Write.as and self-hosted WriteFreely instances

## Installation

### Installing `uv` or `uvx`

If you don't have `uv` or `uvx` installed, you can install them using one of the following methods:

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Using Homebrew (macOS):**
```bash
brew install uv
```

**Using pip:**
```bash
pip install uv
```

After installation, `uvx` will be available as part of `uv`. See the [uv documentation](https://github.com/astral-sh/uv) for more details.

### Using `uvx` (recommended)

```bash
uvx --from writefreely-mcp-server writefreely-mcp
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
      "args": ["--from", "writefreely-mcp-server", "writefreely-mcp"],
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
- `browse_public_feed()` - Browse the public feed

## License

MIT

## Links

- [Development](https://github.com/laxmena/writefreely-mcp-server/blob/main/DEVELOPMENT.md)
- [Contributing](https://github.com/laxmena/writefreely-mcp-server)
- [Issues](https://github.com/laxmena/writefreely-mcp-server/issues)
