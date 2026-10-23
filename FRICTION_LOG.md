# Friction Log

## 1. MCP Python SDK 2.x broke FastMCP imports
- **Task:** Run an MCP server over Streamable HTTP.
- **Steps:** `pip install mcp`, then `from mcp.server.fastmcp import FastMCP`.
- **Expected:** The standard FastMCP quickstart works.
- **Actual:** `ModuleNotFoundError: No module named 'mcp.server.fastmcp'` (v2 renamed it to MCPServer). The client import `streamablehttp_client` was also renamed.
- **Severity:** Medium
- **Workaround:** Pin `mcp>=1.9,<2` in requirements.txt.
- **Suggestion:** Add a version note to quickstarts and a clear error message pointing to the migration guide.

## 2. Opening the MCP endpoint in a browser looks like a failure
- **Task:** Check that the server is running by opening /mcp.
- **Expected:** Some confirmation page.
- **Actual:** `406 Not Acceptable`, which is correct for MCP clients but confusing for newcomers.
- **Severity:** Low
- **Workaround:** Added a home page route at `/` and a `test_client.py`.
- **Suggestion:** Return a short human-readable hint for browser GET requests.
