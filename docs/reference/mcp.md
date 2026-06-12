# Reference: MCP

The `MCPClient` and config schema. Requires `pip install 'aisuite[mcp]'`. Import from `aisuite.mcp`.

## MCPClient

```python
MCPClient(command=None, args=None, env=None, server_url=None,
          headers=None, timeout=30.0, name=None)
```

| Parameter | Type | Transport | Description |
|-----------|------|-----------|-------------|
| `command` | str \| None | stdio | Command to launch the server (e.g. `"npx"`). |
| `args` | list[str] \| None | stdio | Command arguments. |
| `env` | dict[str,str] \| None | stdio | Environment for the server process. |
| `server_url` | str \| None | HTTP | Base URL (e.g. `"http://localhost:8000"`). |
| `headers` | dict[str,str] \| None | HTTP | HTTP headers (auth). |
| `timeout` | float | HTTP | Request timeout (seconds, default 30.0). |
| `name` | str \| None | both | Name for logging and tool prefixing. |

Provide exactly one transport: `command` (stdio) **or** `server_url` (HTTP).

### Methods

| Method | Description |
|--------|-------------|
| `get_callable_tools(allowed_tools=None, use_tool_prefix=False) -> list[Callable]` | Return the server's tools as aisuite-compatible callables. `allowed_tools` whitelists by name; `use_tool_prefix` names them `<name>__<tool>`. |
| `close()` | Close the connection (stdio or HTTP). |
| `from_config(config: dict) -> MCPClient` | (classmethod) Build a client from an MCP config dict. |

`MCPClient` is a context manager: `with MCPClient(...) as mcp:` calls `close()` on exit.

## MCP config dict

Used inline in `tools=[...]` or with `MCPClient.from_config(...)`.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `type` | `"mcp"` | yes | — | Marks the dict as MCP config. |
| `name` | str | yes | — | Non-empty identifier. |
| `command` | str | stdio | — | Server launch command. |
| `args` | list[str] | no | `[]` | Command arguments. |
| `env` | dict | no | — | Server environment. |
| `cwd` | str | no | — | Server working directory. |
| `server_url` | str | HTTP | — | `http(s)://...` base URL. |
| `headers` | dict | no | — | HTTP headers. |
| `timeout` | number | no | — | HTTP request timeout (seconds). |
| `allowed_tools` | list[str] | no | all | Tool-name whitelist. |
| `use_tool_prefix` | bool | no | False | Prefix tool names with `<name>__`. |
| `timeout_seconds` | int | no | 30 | Per-call timeout. |
| `response_bytes_cap` | int | no | 10485760 (10 MB) | Max bytes per tool response. |
| `lazy_connect` | bool | no | False | Defer connection until first tool call. |

Provide `command` **or** `server_url`, not both.

### Helper functions

| Function | Description |
|----------|-------------|
| `is_mcp_config(obj) -> bool` | True if `obj` is a dict with `type == "mcp"`. |
| `validate_mcp_config(config) -> MCPConfig` | Validate and apply defaults; raises `ValueError` on bad config. |
| `get_transport_type(config) -> "stdio" \| "http"` | `"stdio"` if `command` present, else `"http"`. |

## Transports

| Transport | Mechanism |
|-----------|-----------|
| stdio | Launches the server as a subprocess; communicates over stdin/stdout via the `mcp` SDK's `stdio_client`. |
| HTTP | `httpx.AsyncClient`; JSON-RPC 2.0 requests, SSE responses; a session id from the `Mcp-Session-Id` header persists across requests. |

## Schema conversion

The server advertises each tool with a JSON Schema input spec. aisuite converts it to a Python callable (`MCPToolWrapper`):

- JSON Schema types → Python annotations; non-`required` params become `Optional`.
- A synthesized `__signature__`, `__doc__`, and `__annotations__`.
- The original schema preserved on `__mcp_input_schema__`, so the `Tools` layer uses the server's exact schema rather than round-tripping it.
- On call, `None` arguments are filtered out before invoking `call_tool`.

## Errors

| Error | Cause |
|-------|-------|
| `ImportError` | `aisuite[mcp]` not installed but an MCP config was used. |
| `ValueError: Failed to create MCP client from config` | Malformed config dict. |

## Related

- [MCP concept](../concepts/mcp.md)
- [Guide: connect an MCP server](../guides/connect-an-mcp-server.md)
