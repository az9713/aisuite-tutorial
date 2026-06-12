# Connect an MCP server

Give a model the tools from any Model Context Protocol server — a filesystem server, a database server, your own — without writing tool functions.

**When you need this:** reusing existing MCP servers, or sharing one tool implementation across MCP-compatible apps (Claude Desktop, Cursor, aisuite).

## Prerequisites

- `pip install 'aisuite[mcp]'`.
- For npx-based servers: Node.js (`npx --version`).
- The server's launch details (a `command` + `args` for stdio, or a `server_url` for HTTP).

## Option A: inline config (one-off)

Drop an MCP config dict into `tools`. aisuite connects, extracts the tools, and closes the connection automatically when the call returns:

```python
import aisuite as ai
client = ai.Client()

response = client.chat.completions.create(
    model="openai:gpt-4o",
    messages=[{"role": "user", "content": "List the files in /docs"}],
    tools=[{
        "type": "mcp",
        "name": "filesystem",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/docs"],
    }],
    max_turns=3,
)
print(response.choices[0].message.content)
```

## Option B: explicit client (reuse)

Create the client once, reuse it, and control filtering. Use it as a context manager so the connection closes cleanly:

```python
from aisuite.mcp import MCPClient

with MCPClient(command="npx",
               args=["-y", "@modelcontextprotocol/server-filesystem", "/docs"]) as mcp:
    tools = mcp.get_callable_tools(
        allowed_tools=["read_file", "list_directory"],  # only expose these
        use_tool_prefix=True,                             # name them filesystem__read_file
    )
    response = client.chat.completions.create(
        model="openai:gpt-4o",
        messages=[{"role": "user", "content": "Read /docs/readme.md"}],
        tools=tools,
        max_turns=3,
    )
```

## Option C: HTTP transport

For a server reachable over HTTP (with auth):

```python
mcp = MCPClient(
    server_url="http://localhost:8000",
    headers={"Authorization": "Bearer YOUR_TOKEN"},
    timeout=30.0,
)
tools = mcp.get_callable_tools()
# ... use tools ...
mcp.close()
```

## With the Agents API

MCP tools attach to an agent like any other tool — get them from an `MCPClient` and pass them in:

```python
from aisuite import Agent, Runner
from aisuite.mcp import MCPClient

mcp = MCPClient(command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", "/docs"])
agent = Agent(name="doc-helper", model="anthropic:claude-sonnet-4-6",
              tools=mcp.get_callable_tools())
result = Runner.run_sync(agent, "Summarize /docs/readme.md")
mcp.close()
```

## Verification

Check the server connected and advertised tools:

```python
with MCPClient(command="npx", args=["-y", "@modelcontextprotocol/server-filesystem", "/docs"]) as mcp:
    tools = mcp.get_callable_tools()
    print([t.__name__ for t in tools])   # the server's tool names
```

Then run a completion and confirm the model invoked one (inspect `response.choices[0].message.tool_calls` or the agent's `steps`).

## Troubleshooting

**`ImportError: MCP tools require the 'mcp' package`** — run `pip install 'aisuite[mcp]'`.

**The server never starts (stdio)** — `npx` isn't on PATH, or the package name is wrong. Test the exact command in your shell first: `npx -y @modelcontextprotocol/server-filesystem /docs`.

**`Failed to create MCP client from config`** — the config dict is malformed. It needs `type: "mcp"`, a non-empty `name`, and exactly one of `command` or `server_url`.

**Tool-name collisions across servers** — set `use_tool_prefix=True` so names become `<name>__<tool>`.

**Responses truncated** — a large tool result hit `response_bytes_cap` (default 10 MB). Raise it in the config if you genuinely need bigger responses.

## Related

- [MCP concept](../concepts/mcp.md) — transports, config schema, how schemas convert.
- [reference/mcp.md](../reference/mcp.md) — `MCPClient` API in full.
- Examples: `examples/mcp_tools_example.ipynb`, `examples/mcp_http_example.py`.
