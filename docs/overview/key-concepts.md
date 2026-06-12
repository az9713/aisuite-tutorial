# Key concepts

Definitions for every term that appears across the docs. Grouped by layer.

## Chat Completions layer

**Client** — The entry point, created with `ai.Client()`. Holds provider configurations and exposes `chat.completions.create(...)` and `audio.transcriptions.create(...)`. Providers are initialized lazily on first use.

**Model string** — A `provider:model` identifier such as `openai:gpt-4o` or `anthropic:claude-sonnet-4-6`. The part before the colon selects the provider adapter; the part after is passed through to that provider. A model string without a colon raises `ValueError`.

**Provider** — An adapter that translates aisuite's unified request into a specific vendor's SDK call and normalizes the response back. Each lives in `aisuite/providers/<name>_provider.py` as a class `<Name>Provider`. Example: `anthropic` → `anthropic_provider.py` → `AnthropicProvider`.

**ProviderFactory** — The discovery mechanism. It maps a provider key to a module and class by naming convention and instantiates it. `get_supported_providers()` globs the providers directory, so adding a correctly named file is all it takes to register a new provider.

**ChatCompletionResponse** — The normalized response object. `response.choices[0].message.content` is the text; `response.usage` carries token counts. Shaped to match the OpenAI response so existing code ports cleanly.

**Message** — A normalized message with `role` (`user` / `assistant` / `system` / `tool`), `content`, optional `tool_calls`, optional `reasoning_content` (extended thinking), and optional `refusal`.

**Extra param mode** — How the client handles unknown audio-transcription parameters: `strict` (raise), `warn` (default, log), or `permissive` (pass through). Set via `ai.Client(extra_param_mode=...)`.

## Tool calling

**Tool** — A plain Python function (or an OpenAI-format JSON spec) exposed to the model. aisuite generates the JSON schema from the function's signature and docstring.

**Tools class** — `ai.Tools` (or the internal registry the client builds) turns callables into provider-ready schemas, validates the model's arguments with a Pydantic model, executes the function, and formats results back as `tool` messages.

**`max_turns`** — The cap on automatic back-and-forth tool rounds. With `max_turns` set, aisuite runs the full loop (send → execute tools → return results → repeat). Omit it to get manual control: aisuite returns the model's tool-call requests and you run the loop.

**`intermediate_messages`** — On `response.choices[0]`, the full history of the tool interaction (assistant tool-call messages plus `tool` result messages). Append it to your messages to continue the conversation.

## Agents API

**Agent** — A declarative definition: `name`, `model`, optional `instructions`, `tools`, `model_settings`, `tags`, and `metadata`. An Agent holds no run state; it is a reusable blueprint.

**Runner** — The executor. `Runner.run(agent, input)` (async) and `Runner.run_sync(...)` run an agent to completion; `Runner.continue_run` / `continue_sync` resume a prior run. The Runner sets up tracing context, drives the tool loop, applies policies, and persists state.

**RunResult** — What a run returns: `final_output`, `status`, `messages`, `steps`, `raw_responses`, `trace_id`, and grouping metadata. Call `to_state()` to get a persistable `RunState`.

**RunState** — A serializable snapshot of a conversation thread: `agent_name`, `messages`, `status`, `steps`, and `max_turns`. This is what state stores persist.

**RunStep** — One recorded step in a run, typed as `agent`, `model_response`, `tool_call`, `tool_result`, `handoff`, or `custom`.

**RunStatus** — A run's terminal state: `completed`, `requires_input` (waiting on a human, e.g. an approval), `max_turns_exceeded`, or `failed`.

**agent_tool** — Wraps an `Agent` as a callable tool so one agent can invoke another (subagents). The subagent inherits the parent's client, trace, policy, and stores via the active run context.

## Tool policies

**Tool policy** — An object (or callable) that decides whether a given tool call may run. It receives a `ToolPolicyContext` and returns a `ToolPolicyDecision`.

**ToolPolicyContext** — The information a policy sees: `agent_name`, `tool_name`, `arguments`, the message history, run metadata, and the tool's `ToolMetadata`.

**ToolPolicyDecision** — `allowed: bool` plus an optional `reason` and `metadata`.

**Built-in policies** — `AllowAllToolPolicy`, `DenyAllToolPolicy`, `AllowToolsPolicy` (allowlist), and `RequireApprovalPolicy` (calls your approval callback).

**ToolMetadata** — Metadata attached to a tool with the `@tool` decorator: `category`, `risk_level` (`low` / `medium` / `high`), `capabilities`, `requires_approval`, and `description`.

## State, artifacts, threads

**State store** — Persists `RunState` keyed by `thread_id` so a conversation can resume across processes. Implementations: `InMemoryStateStore`, `FileStateStore`, `PostgresStateStore`.

**Thread** — A persisted conversation, identified by a `thread_id`. Pass `state_store` + `thread_id` to `Runner.run_sync` to create one, and to `continue_sync` to resume it.

**Optimistic concurrency** — State stores version each thread with a `revision` integer. Saving with a stale revision raises `StateConflictError`, so concurrent writers can't silently clobber each other.

**Compaction** — Summarizing a range of older messages into one summary message to keep within the context window. Recorded as a `CompactionRecord` (Postgres store).

**Artifact** — A blob (bytes plus a media type) stored out-of-band and referenced from messages. Large fields (long file contents, diffs, stdout) are "dehydrated" into artifact references and "hydrated" back before a model call.

**Artifact store** — Where artifacts live: `InMemoryArtifactStore` or `FileArtifactStore`. Artifacts are addressed by `ArtifactRef` with a `uri` like `memory://...` or `artifact://...`.

## Toolkits

**Toolkit** — A prebuilt, sandboxed family of tools returned as a list of callables ready to attach to an agent. Three ship in the box: `files`, `git`, `shell`.

**Root confinement** — Toolkits resolve every path against a configured root and refuse paths that escape it (raising `PermissionError`). This is the sandbox boundary.

**files toolkit** — Read tools (`list_files`, `read_file`, `read_file_lines`, `search_files`) and, when writing is enabled, approval-gated write tools (`write_file`, `apply_unified_diff`, `apply_patch`, `replace_in_file`).

**git toolkit** — Read-only repo inspection: `git_status` and `git_diff`.

**shell toolkit** — A single high-risk, approval-gated `run_shell` tool, restricted to an allowlist of commands unless `allow_all=True`, with shell metacharacters blocked unless `allow_shell=True`.

## MCP

**MCP (Model Context Protocol)** — An open protocol for exposing tools from a separate server process. aisuite can consume any MCP server's tools. See [modelcontextprotocol.io](https://modelcontextprotocol.io/docs/getting-started/intro).

**MCPClient** — aisuite's MCP connection. Created directly or via `from_config`. Speaks two transports: **stdio** (launch a server with `command`/`args`) and **HTTP** (`server_url`/`headers`). `get_callable_tools(...)` returns the server's tools as aisuite-compatible callables.

**MCP config dict** — An inline tool spec `{"type": "mcp", "name": ..., "command"|"server_url": ...}` you can drop into the `tools=[...]` list; the client converts it to callable tools and cleans up the connection automatically.

**Tool prefixing** — Optionally namespacing MCP tool names as `<client_name>__<tool>` to avoid collisions when several servers expose same-named tools.

## Tracing

**Trace event** — A `TraceEvent` emitted at each significant moment: `run.started`/`completed`/`failed`, `model.send`/`response`/`error`, `tool.allowed`/`denied`/`started`/`completed`/`failed`.

**Trace sink** — A destination for events. Built-ins: `LocalTraceSink` (JSONL file), `InMemoryTraceSink`, `HttpTraceSink` (POST to an endpoint), `TraceStoreSink`.

**Trace store** — Where events are persisted and reconstructed into runs: `JsonlTraceStore` or `InMemoryTraceStore`.

**trace_id / group_id / run_name / parent_run_id** — Identity and grouping. `trace_id` identifies one run; `group_id` ties related runs together; `run_name` is human-readable; `parent_run_id` links a subagent run to its parent.

**Viewer** — A local web UI (`aisuite/tracing/viewer.py`, served from `aisuite/tracing/static/viewer/`) that reads traces and renders timelines, transcripts, and artifacts. The source lives in [`viewer-ui/`](../components/viewer-ui.md).

## Components

**OpenCoworker** — The desktop AI coworker built on aisuite, source under `platform/`. A FastAPI + React (Tauri) application with approvals, scheduled automations, connectors, and MCP.

**aisuite-code CLI** — A local coding-agent CLI under `cli/py/`, scoped to a project directory with approval-gated file/shell tools.

**aisuite-js** — A TypeScript port of the Chat Completions layer (npm package `aisuite`).
