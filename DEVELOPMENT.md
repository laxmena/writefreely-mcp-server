# Development Guide

This document contains information for developers who want to contribute to or modify the writefreely-mcp-server project.

## Setup

Clone the repository and install dependencies:

```bash
git clone https://github.com/laxmena/writefreely-mcp-server.git
cd writefreely-mcp-server
uv sync
```

This will install all dependencies including development dependencies.

## Running the MCP Server

Run the MCP server using `uv`:

```bash
uv run writefreely-mcp
```

**Note:** The server runs using stdio transport, which means it communicates via standard input/output. This is the standard way MCP servers work. To test it, you'll need to use an MCP client or the MCP Inspector.

### Environment Variables

Set environment variables before running:

```bash
export WRITEFREELY_BASE_URL="https://write.as"
export WRITEFREELY_ACCESS_TOKEN="your_token_here"
export WRITEFREELY_DEFAULT_LANGUAGE="en"
```

Or run with inline environment variables:

```bash
WRITEFREELY_BASE_URL="https://write.as" WRITEFREELY_ACCESS_TOKEN="your_token" uv run writefreely-mcp
```

## Running Tests

Run the test suite with pytest:

```bash
uv run pytest
```

For more verbose output:

```bash
uv run pytest -v
```

## Using the MCP Inspector

The MCP Inspector is a visual tool for testing and debugging MCP servers. To run it with the WriteFreely MCP server:

```bash
npx --yes @modelcontextprotocol/inspector uv run writefreely-mcp
```

Or with environment variables:

```bash
WRITEFREELY_BASE_URL="https://write.as" WRITEFREELY_ACCESS_TOKEN="your_token" npx --yes @modelcontextprotocol/inspector uv run writefreely-mcp
```

The Inspector will:
- Start a web UI at `http://localhost:6274` (open in your browser)
- Start a proxy server on port `6277` for communication
- Automatically launch your MCP server

You can then interact with your server through the web interface, test tools, and view responses in real-time.

**Finding Logs:**

When running the MCP Inspector, server logs appear in the terminal where you ran the `npx` command. The server uses Python's logging module and outputs INFO level and above messages to stdout/stderr.

To see more detailed logs, you can set the `LOG_LEVEL` environment variable:

```bash
LOG_LEVEL=DEBUG npx --yes @modelcontextprotocol/inspector uv run writefreely-mcp
```

This will show DEBUG level logs including detailed API request/response information.

## Code Quality

### Linting

Check code style and quality with ruff:

```bash
uv run ruff check .
```

To automatically fix issues:

```bash
uv run ruff check --fix .
```

### Type Checking

Run mypy for type checking:

```bash
uv run mypy src/
```

## Project Structure

```
writefreely-mcp-server/
├── src/
│   └── writefreely_mcp_server/
│       ├── __init__.py
│       ├── api_client.py      # Low-level HTTP client for WriteFreely API
│       ├── config.py           # Configuration and environment variables
│       ├── server.py           # Main MCP server entry point
│       └── tools/              # MCP tool implementations
│           ├── __init__.py
│           ├── auth.py         # Authentication tools
│           ├── collections.py  # Collection/blog management tools
│           ├── feed.py         # Public feed tools
│           └── posts.py        # Post management tools
├── src/tests/                  # Test files
├── pyproject.toml              # Project configuration and dependencies
└── README.md                   # User-facing documentation
```

## Architecture

The server is built using the FastMCP framework and follows a modular structure:

- **api_client.py**: Contains all low-level API calls to the WriteFreely API using httpx
- **config.py**: Manages configuration from environment variables
- **tools/**: Each module registers MCP tools that wrap API client functions
- **server.py**: Main entry point that registers all tools and starts the MCP server

## Adding New Tools

To add a new tool:

1. Add the API function to `api_client.py` if needed
2. Create or update the appropriate tool module in `tools/`
3. Register the tool using the `@mcp.tool()` decorator
4. Import and register the tool module in `server.py`

Example:

```python
# In tools/posts.py
@mcp.tool()
async def my_new_tool(param: str) -> str:
    """
    Description of what the tool does.
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
    """
    try:
        result = await api_client.my_api_function(param)
        return f"Success: {result}"
    except WriteAsError as e:
        return f"Error: {str(e)}"
```

## Environment Variables

The following environment variables are used:

- `WRITEFREELY_BASE_URL`: Base URL for WriteFreely instance (default: `https://write.as`)
- `WRITEFREELY_ACCESS_TOKEN`: Access token for authentication
- `WRITEFREELY_DEFAULT_LANGUAGE`: Default language for posts (default: `en`)

## Testing

Tests are located in `src/tests/`. When adding new features, please add corresponding tests.

Run tests with coverage:

```bash
uv run pytest --cov=src/writefreely_mcp_server --cov-report=html
```

## Pre-commit Hooks

The project uses pre-commit hooks for code quality. Install them:

```bash
uv run pre-commit install
```

## Building and Publishing

Build the package:

```bash
uv build
```

This will create distribution files in the `dist/` directory.

### Publishing to PyPI

To publish the package to PyPI, you'll need to install `twine`:

```bash
# Install twine
uv pip install twine
# Or: pip install twine
```

**First, test on Test PyPI:**

```bash
# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Test installation
uv pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ writefreely-mcp-server
```

**Then publish to production PyPI:**

```bash
# Upload to production PyPI
twine upload dist/*
```

**Note:** You'll need PyPI accounts:
- Test PyPI: https://test.pypi.org/account/register/
- Production PyPI: https://pypi.org/account/register/

For authentication, you can use API tokens instead of passwords:
- Create tokens at https://pypi.org/manage/account/token/
- Use: `twine upload --username __token__ --password pypi-... dist/*`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Ensure all tests pass and code quality checks pass
6. Submit a pull request

Please ensure your code follows the existing style and includes appropriate documentation.
