# MCP (Model Context Protocol)

aisuite natively consumes [Model Context Protocol](https://modelcontextprotocol.io/docs/getting-started/intro) servers, so any MCP server's tools can be handed to a model without boilerplate. Install the extra: `pip install 'aisuite[mcp]'`.

## What it is

MCP is an open protocol for exposing tools (and other capabilities) from a separate server process. Instead of writing Python functions, you point aisuite at a server — launched as a subprocess (stdio) or reached over HTTP — and it turns the server's tools into aisuite-compatible callables.

## Two ways to use it

### Inline config (simplest)

Drop an MCP config dict straight into the `tools=[...]` list. aisuite detects it, connects, extracts the tools, and cleans up the connection automatically when the call finishes:

```python
response = client.chat.completions.create(
    model="openai:gpt-4o",
    messages=[{"role": "user", "content": "List the files in the current directory"}],
    tools=[{
        "type": "mcp",
        "name": "filesystem",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/directory"],
    }],
    max_turns=3,
)
```

### Explicit client (reusable)

Create an `MCPClient` once, reuse it across calls, and apply filtering or prefixing:

```python
from aisuite.mcp import MCPClient

mcp = MCPClient(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/path/to/directory"],
)
response = client.chat.completions.create(
    model="openai:gpt-4o",
    messages=[{"role": "user", "content": "List the files"}],
    tools=mcp.get_callable_tools(),
    max_turns=3,
)
mcp.close()
```

`MCPClient` is a context manager, so `with MCPClient(...) as mcp:` closes the connection for you.

## Transports

A client speaks exactly one transport, chosen by which fields you provide:

| Transport | Fields | When |
|-----------|--------|------|
| **stdio** | `command`, `args`, `env` | Launch a local server process (most npx/python servers) |
| **HTTP** | `server_url`, `headers`, `timeout` | Connect to a running server, with auth headers; supports JSON-RPC + SSE |

Provide `command` *or* `server_url`, never both.

## The config dict

```python
{
    "type": "mcp",            # required, always "mcp"
    "name": "filesystem",     # required, non-empty

    # stdio transport
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/docs"],
    "env": {"FOO": "bar"},
    "cwd": "/work",

    # OR http transport
    "server_url": "http://localhost:8000",
    "headers": {"Authorization": "Bearer ..."},
    "timeout": 30,

    # filtering & namespacing
    "allowed_tools": ["read_file", "list_directory"],  # whitelist
    "use_tool_prefix": False,                           # name as "<name>__<tool>"

    # safety limits
    "timeout_seconds": 30,
    "response_bytes_cap": 10485760,   # 10 MB
    "lazy_connect": False,
}
```

`is_mcp_config(obj)` is how aisuite recognizes one (a dict with `type == "mcp"`). `validate_mcp_config(...)` checks required fields and applies defaults.

## Filtering and prefixing

`get_callable_tools(allowed_tools=None, use_tool_prefix=False)`:

- **`allowed_tools`** — a whitelist of tool names to expose. `None` exposes everything the server offers. Use it to give a model only the subset it needs.
- **`use_tool_prefix`** — when `True`, tool names become `<client_name>__<tool>`, avoiding collisions when several servers expose same-named tools.

## How server tools become callables

The MCP server advertises each tool with a JSON Schema input spec. aisuite's `schema_converter` turns that into a Python callable: it maps JSON Schema types to annotations (marking non-required parameters `Optional`), synthesizes a signature and docstring, and wraps the whole thing in an `MCPToolWrapper`. Crucially, the wrapper preserves the original MCP schema on `__mcp_input_schema__`, so the [`Tools`](tool-calling.md) layer can use the server's exact schema rather than round-tripping it. From the model's perspective an MCP tool is indistinguishable from a native Python tool.

## Safety limits

`response_bytes_cap` (default 10 MB) bounds how much a single tool response can return, and `timeout_seconds` bounds how long a call may run — guarding against a misbehaving server flooding or stalling your run.

## Related

- [Tool calling](tool-calling.md) — MCP tools share the same execution path as native tools.
- [Guide: connect an MCP server](../guides/connect-an-mcp-server.md).
- [reference/mcp.md](../reference/mcp.md) — `MCPClient` API and config schema in full.
- Examples: `examples/mcp_tools_example.ipynb`, `examples/mcp_config_dict_example.py`, `examples/mcp_http_example.py`.
