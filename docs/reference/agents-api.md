# Reference: Agents API

`Agent`, `Runner`, and the run data types. Import from `aisuite`.

## Agent

```python
Agent(*, name, model, instructions=None, tools=[], model_settings={}, tags=[], metadata={})
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | str | — | Identifier; used in traces and as a subagent tool name. |
| `model` | str | — | A `provider:model` string. |
| `instructions` | str \| None | None | System prompt. |
| `tools` | list[Callable] | `[]` | Tools and toolkit functions. |
| `model_settings` | dict | `{}` | Extra kwargs merged into each model call. |
| `tags` | list[str] | `[]` | Labels propagated to traces. |
| `metadata` | dict | `{}` | Metadata propagated to traces. |

A keyword-only dataclass holding no run state.

## Runner

All methods are static.

### Runner.run / run_sync

```python
await Runner.run(agent, input, *, client=None, max_turns=5, run_name=None,
                 parent_run_id=None, group_id=None, tags=None, metadata=None,
                 tool_policy=None, trace_sinks=None, tracing_disabled=False,
                 state_store=None, thread_id=None, artifact_store=None, **kwargs) -> RunResult

Runner.run_sync(...)   # same signature, synchronous
```

`run` is async and delegates to `run_sync`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `agent` | Agent | — | The agent to execute. |
| `input` | str \| list[dict] \| RunState | — | New input, or a `RunState` to resume. |
| `client` | Client \| None | new `Client()` | LLM client. |
| `max_turns` | int | 5 | Tool-loop cap. |
| `run_name` | str \| None | None | Human-readable run name. |
| `parent_run_id` | str \| None | None | Parent run's trace id (for nesting). |
| `group_id` | str \| None | None | Group related runs. |
| `tags` | list[str] \| None | agent's | Trace tags. |
| `metadata` | dict \| None | agent's | Trace metadata. |
| `tool_policy` | ToolPolicy \| Callable \| None | None | Gate tool calls. |
| `trace_sinks` | list[TraceSink] \| None | configured | Override trace destinations. |
| `tracing_disabled` | bool | False | Disable tracing for this run. |
| `state_store` | StateStore \| None | None | Persist the thread (requires `thread_id`). |
| `thread_id` | str \| None | None | Thread identifier (requires `state_store`). |
| `artifact_store` | ArtifactStore \| None | None | Offload large message payloads. |
| `**kwargs` | — | — | Merged into `agent.model_settings`. |

`state_store` and `thread_id` must be supplied together (or neither) → otherwise `ValueError`. Creating an existing thread → `ThreadAlreadyExistsError`.

### Runner.continue_run / continue_sync

```python
await Runner.continue_run(target, input, **overrides) -> RunResult

Runner.continue_sync(target, input, *, state_store=None, thread_id=None,
                     artifact_store=None, **overrides) -> RunResult
```

| `target` | Behavior |
|----------|----------|
| A `RunResult` | In-memory continuation: appends `input` to the prior result's state and re-runs with the same client and agent. |
| An `Agent` | Persisted continuation: requires `state_store` + `thread_id`; loads the stored thread, appends `input`, re-runs, and saves back with optimistic concurrency. |

Resuming a missing thread → `StateNotFoundError`.

## RunResult

| Field | Type | Description |
|-------|------|-------------|
| `final_output` | Any | The agent's last output. |
| `status` | RunStatus | `completed` \| `requires_input` \| `max_turns_exceeded` \| `failed`. |
| `agent` / `last_agent` | Agent | Initial and final agent (differ if a handoff occurred). |
| `input` | str \| list \| RunState | The original input. |
| `messages` | list[dict] | Full message history. |
| `new_items` | list[dict] | Items produced this run. |
| `raw_responses` | list | Raw provider responses. |
| `steps` | list[RunStep] | Ordered run steps. |
| `trace_id` | str | This run's trace id. |
| `run_name`, `parent_run_id`, `group_id`, `tags`, `metadata` | — | Trace identity. |
| `max_turns` | int | The turn cap used. |

Methods: `to_state() -> RunState`, `trace_to_dict() -> dict`, `write_trace_jsonl(path)`, `print_trace(file=None)`.

## RunState

A serializable thread snapshot.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `agent_name` | str | — | Owning agent. |
| `messages` | list[dict] | — | Conversation history. |
| `status` | RunStatus | `completed` | Terminal status. |
| `run_name`, `trace_id`, `parent_run_id`, `group_id` | str \| None | None | Identity. |
| `tags` | list[str] | `[]` | Labels. |
| `metadata` | dict | `{}` | Metadata. |
| `steps` | list[RunStep] | `[]` | Recorded steps. |
| `max_turns` | int | 5 | Turn cap. |

Methods: `add_user_message(input)`, `to_dict()`, `from_dict(data)`. Values must be JSON-serializable or `to_dict()` raises `TypeError`.

## RunStep

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Step id. |
| `type` | RunStepType | `agent` \| `model_response` \| `tool_call` \| `tool_result` \| `handoff` \| `custom`. |
| `name` | str \| None | Step name (e.g. the tool name). |
| `trace_id` | str | Owning trace. |
| `parent_id` | str \| None | Parent step. |
| `started_at` / `ended_at` | str | Timestamps. |
| `data` | dict | Step payload (e.g. `allowed`, `reason`, `status`). |

## Subagents

```python
agent_tool(agent, *, name=None, description=None) -> Callable
```

Wraps an `Agent` as a callable tool. When invoked, the subagent runs via `Runner.run_sync` inheriting the parent's client, `trace_id` (as `parent_run_id`), `group_id`, tags, metadata, `tool_policy`, `trace_sinks`, and `artifact_store` from the active run context. Returns the subagent's `final_output` as a string.

## Exceptions

| Exception | Raised when |
|-----------|-------------|
| `ThreadAlreadyExistsError` | `run_sync` targets a `thread_id` that already exists. |
| `StateNotFoundError` | `continue_sync` finds no thread for the id. |
| `StateConflictError` | A save hits a stale revision (see [stores](policies-and-stores.md)). |

## Related

- [Agents API concept](../concepts/agents-api.md)
- [reference/policies-and-stores.md](policies-and-stores.md)
- [reference/client-api.md](client-api.md)
