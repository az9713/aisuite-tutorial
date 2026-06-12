# System design

How aisuite is built, for developers who will work on it (not just use it). The reader-facing concepts live in [concepts/](../concepts/); this is the architecture beneath them.

## High-level architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        OpenCoworker                          │
│        (platform/ — FastAPI + React, approvals, cron)        │
└───────────────────────────────┬──────────────────────────────┘
                                 │ builds on
┌───────────────────────────────▼──────────────────────────────┐
│                         Agents layer                         │
│  Agent · Runner · ToolPolicy · StateStore · ArtifactStore    │
│  ──────────────────────────────────────────────────────────  │
│  Runner sets a ContextVar run-context, then calls ↓          │
└───────────────────────────────┬──────────────────────────────┘
                                 │
┌───────────────────────────────▼──────────────────────────────┐
│                   Chat Completions layer                     │
│  Client → Completions.create → _tool_runner (max_turns loop) │
│  Tools (fn→schema), MCP config expansion, tracing emit       │
└───────────────────────────────┬──────────────────────────────┘
                                 │ ProviderFactory (convention discovery)
┌───────────────────────────────▼──────────────────────────────┐
│                      Provider adapters                       │
│  OpenAI · Anthropic · Google · Bedrock · 20+ others          │
│  each → normalized ChatCompletionResponse                    │
└──────────────────────────────────────────────────────────────┘

   Cross-cutting: Tracing (sinks → stores → viewer-ui)
```

## Component breakdown

| Component | Module | Responsibility |
|-----------|--------|----------------|
| Client | `aisuite/client.py` | Parse `provider:model`, lazily build providers, run the `max_turns` tool loop, expand MCP configs, emit trace events. |
| ProviderFactory | `aisuite/provider.py` | Convention-based discovery and instantiation of providers. |
| Provider adapters | `aisuite/providers/*_provider.py` | Translate to/from each vendor; output a normalized response. |
| Framework types | `aisuite/framework/` | `ChatCompletionResponse`, `Choice`, `Message`, `CompletionUsage`, ASR types, parameter mappers. |
| Tools | `aisuite/utils/tools.py` | Function→schema generation (docstring + signature), Pydantic validation, execution, policy evaluation, tool-event emission. |
| Agents | `aisuite/agents/` | `Agent`, `Runner`, policies, state stores, artifact stores, run context, subagents. |
| MCP | `aisuite/mcp/` | stdio/HTTP MCP clients, config validation, schema→callable conversion. |
| Tracing | `aisuite/tracing/` | Event types, sinks, stores, normalization, the viewer server. |
| Toolkits | `aisuite/toolkits/` | Sandboxed files/git/shell tool families. |

## Data flows

### A chat completion

1. `Client.chat.completions.create(model, messages, **kwargs)` splits `model`, validates the provider, lazily instantiates the adapter.
2. If `tools` contains MCP config dicts, they're expanded into callables and the MCP clients are registered on an `ExitStack` for automatic cleanup.
3. With `max_turns` + `tools`: `_tool_runner` loops — call provider, check `tool_calls`, execute via `Tools.execute_tool` (applying any policy), append results, repeat.
4. Without `max_turns`: a single provider call; tool schemas are still passed so the model can request calls you'll run yourself.
5. The response is post-processed (`<think>` extraction) and returned.

### An agent run

1. `Runner.run_sync(agent, input, ...)` resolves the input (fresh, or a `RunState` to resume), hydrating artifact-dehydrated fields.
2. It builds the request (merging `model_settings`), and if a policy is set, a `ToolPolicyContext`.
3. It sets an `ActiveRunContext` in a `ContextVar` (`aisuite/agents/context.py`) — carrying the client, `trace_id`, sinks, policy, and artifact store — then calls the Chat Completions layer.
4. Because the context is a `ContextVar`, the model and tool calls made *inside* the layer below can read it (via `get_active_run_context`) and emit trace events without the agent layer threading anything through.
5. It assembles the `RunResult` (final output, steps, raw responses) and, if a state store is set, dehydrates and saves the `RunState`.

### A subagent call

`agent_tool(child)` wraps an `Agent` as a callable. When invoked it reads the active run context and calls `Runner.run_sync` for the child with the parent's client/trace/group/policy/stores — so the nested run shares the trace tree.

## Key design decisions

These are the non-obvious choices; each has a full ADR.

- **Provider discovery is convention-based**, not a registry. Adding a file is enough. → [ADR 0001](adr/0001-provider-naming-convention.md)
- **Tool schemas are generated from Python functions**, treating the function as the single source of truth. → [ADR 0002](adr/0002-tools-from-python-functions.md)
- **Tool governance is a separate policy primitive**, decoupled from tool definitions, so the same tool can be ungated, allowlisted, or approval-gated by run. → [ADR 0003](adr/0003-tool-policies-and-approvals.md)
- **Tracing is local-first**, emitting to JSONL/memory with a bundled local viewer and no required backend. → [ADR 0004](adr/0004-local-first-tracing.md)

Two further structural choices worth calling out:

- **The run context is a `ContextVar`, not a parameter.** This lets the lower Chat Completions layer participate in tracing and policy without the Agents layer leaking those concerns into `create()`'s signature. It also means context propagates correctly across nested/subagent calls.
- **State and artifacts are separate stores.** State persists *what the conversation is*; artifacts hold *large payloads referenced from it*. Splitting them keeps the persisted message history compact and lets a viewer fetch big blobs on demand.

## Scaling characteristics

| Concern | Behavior |
|---------|----------|
| Providers | Initialized lazily and cached per `Client`. A `TODO` notes provider init isn't yet thread-safe under concurrent first-use of the same provider. |
| State | `InMemoryStateStore` is single-process; `FileStateStore` is single-machine; `PostgresStateStore` supports multi-process with optimistic-concurrency (`revision`) and message-prefix dedup + compaction for long threads. |
| Tracing | Local JSONL append for development; `HttpTraceSink` ships events to a remote collector for production observability. |
| Context window | Postgres compaction summarizes old message ranges into `CompactionRecord`s to stay within limits. |

## External dependencies

- **Required:** `pydantic` (framework types, validation), `docstring-parser` (schema generation), `httpx` (HTTP-style providers).
- **Optional (per extra):** vendor SDKs (`openai`, `anthropic`, `boto3`, `vertexai`, …), `mcp` + `nest-asyncio` (MCP), `psycopg` (Postgres store).

## Related

- [What is aisuite?](../overview/what-is-this.md) — the conceptual version.
- [Concepts](../concepts/) — each subsystem in depth.
- [ADRs](adr/) — the decision records.
