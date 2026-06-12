# OpenCoworker

OpenCoworker is a desktop AI coworker built on aisuite — a downloadable app and the reference harness for building your own. Source: [`platform/`](https://github.com/andrewyng/aisuite/tree/main/platform).

To install and use the app, see the [OpenCoworker quickstart](../opencoworker-quickstart.md). This page is for developers who want to understand or extend the harness.

## What it is

A provider-agnostic agent runtime with a desktop GUI. Point it at a folder, give it a task in plain language, and it researches, analyzes, and produces real files — with approvals before risky actions, scheduled automations, MCP integrations, and a built-in trace viewer. It has no backend: model calls go directly from your machine to the provider you configured, and your keys and data stay local.

It's both a product and a worked example: everything it does is built on the aisuite [Agents API](../concepts/agents-api.md), [toolkits](../concepts/toolkits.md), [tool policies](../concepts/tool-policies.md), [MCP](../concepts/mcp.md), and [tracing](../concepts/tracing.md).

## Tech stack

| Layer | Technology |
|-------|-----------|
| Agent backend | Python 3.10+ |
| HTTP/WS server | FastAPI + uvicorn |
| GUI | React 18 (browser dev; Tauri v2 desktop shell) |
| Scheduling | `croniter` |
| LLM access | aisuite (sourced from the parent worktree, not PyPI) |
| Optional | Playwright (browser), python-telegram-bot / slack-bolt (messaging), ddgs (search) |

## Architecture

```
platform/
├── coworker/                # the agent harness (Python)
│   ├── engine.py            # orchestration
│   ├── agent.py             # agent execution
│   ├── cli.py               # Textual TUI entry point
│   ├── permissions.py       # approval / policy system
│   ├── conversations.py     # session storage & memory
│   ├── server/              # FastAPI app serving the GUI + WS approval stream
│   │   ├── run.py           #   `coworker-server` entry point
│   │   ├── app.py           #   FastAPI app
│   │   └── manager.py       #   session manager
│   ├── automation/          # cron scheduler
│   ├── connectors/          # email, Slack, Telegram, Gmail, Outlook, web search
│   ├── mcp/                 # MCP client layer
│   └── memory/              # SQLite memory store
├── surfaces/gui/            # React + Tauri front end (talks to coworker-server)
├── packaging/               # build/packaging
├── docs/                    # specs (e.g. email-connector-spec.md)
└── tests/
```

Two halves: **`coworker/`** is the engine (CLI, server, connectors, policies, memory); **`surfaces/gui/`** is a thin React client that talks to `coworker-server` over HTTP and WebSocket.

## Entry points

| Command | Entry | Purpose |
|---------|-------|---------|
| `coworker` | `coworker.cli:main` | Terminal UI (Textual). Supports `--cwd`, `--model`, `--mode`, `--resume`. |
| `coworker-server` | `coworker.server.run:main` | HTTP/WS server for the GUI (e.g. `--port 8765`). |
| `coworker-connectors` | `coworker.connectors.cli:main` | Manage connectors. |

## How it maps to aisuite

| OpenCoworker feature | aisuite primitive |
|----------------------|-------------------|
| Multi-provider model switching | [Chat Completions](../concepts/chat-completions.md) `provider:model` routing |
| Doing tasks with tools | [Agents API](../concepts/agents-api.md) + [toolkits](../concepts/toolkits.md) |
| Approval cards before risky actions | [tool policies](../concepts/tool-policies.md) + `requires_input` pause/resume |
| Saving deliverables / large outputs | [artifact stores](../concepts/state-and-artifacts.md) |
| Resuming conversations | [state stores](../concepts/state-and-artifacts.md) |
| Run timeline / inspection | [tracing](../concepts/tracing.md) + the [viewer](viewer-ui.md) |
| Add-your-own integrations | [MCP](../concepts/mcp.md) (`mcpServers` JSON, same format as Claude Desktop / Cursor) |

Reading OpenCoworker is the fastest way to see how the aisuite primitives compose into a real harness.

## Running from source

Run the backend, then the GUI dev server:

```bash
# 1. backend
cd platform
export OPENAI_API_KEY=sk-...
./.venv/bin/coworker-server --cwd /path/to/project --port 8765

# 2. front end (separate terminal)
cd platform/surfaces/gui
npm install
npm run dev          # → http://localhost:5173
```

The GUI talks to `http://127.0.0.1:8765` by default (override with `VITE_COWORKER_HTTP` / `VITE_COWORKER_WS`). The Tauri desktop build runs `coworker-server` as a sidecar subprocess; it requires a Rust toolchain and the `src-tauri/` scaffold.

## Permission modes

Like the CLI, OpenCoworker supports `plan`, `interactive`, and `auto` modes — governing how much it does before pausing for approval. Risky actions (shell commands, writes outside granted folders) always surface an approval card first.

## Related

- [OpenCoworker quickstart](../opencoworker-quickstart.md) — install and first tasks.
- [aisuite-code CLI](cli.md) — the lighter terminal-only sibling.
- [viewer-ui](viewer-ui.md) — the trace viewer it embeds.
