# Tracing

Tracing records every meaningful moment of an agent run — model calls, tool executions, approvals, errors — as structured events you can persist and replay in a local viewer. It's how you debug, audit, and understand what an agent actually did.

## What it is

As a run executes, aisuite emits `TraceEvent`s to configured **sinks**. Sinks write events to a destination (a JSONL file, memory, an HTTP endpoint). A **store** reconstructs those events back into runs, and the **viewer** renders them as timelines and transcripts.

Tracing is automatic inside `Runner.run` — you don't instrument anything. The Runner opens a trace context, and even plain `client.chat.completions.create(...)` calls made within that context emit model events.

## Trace events

Each `TraceEvent` carries identity, grouping, and an event-specific `data` payload. The event types:

| Group | Events |
|-------|--------|
| Run | `run.started`, `run.completed`, `run.failed` |
| Model | `model.send`, `model.response`, `model.error` |
| Tool | `tool.allowed`, `tool.denied`, `tool.started`, `tool.completed`, `tool.failed` |

Model events carry normalized input/output: message counts, modalities (text/image), text previews, finish reason, and token usage. Tool events carry the tool name, arguments, and result/error.

## Identity and grouping

Four fields connect events into a coherent picture:

| Field | Meaning |
|-------|---------|
| `trace_id` | Identifies one run. All of a run's events share it. |
| `run_name` | Human-readable name (defaults to the agent name). |
| `group_id` | Ties related runs together (e.g. several attempts at one task). |
| `parent_run_id` | Links a subagent run to the parent that invoked it. |

Subagent runs inherit `group_id` and set `parent_run_id` to the parent's `trace_id`, so a multi-agent run renders as one connected tree.

## Sinks

A sink implements `emit(event) -> None`. Built-ins:

| Sink | Destination |
|------|-------------|
| `LocalTraceSink(path=".aisuite/events.jsonl")` | a local JSONL file |
| `InMemoryTraceSink()` | an in-memory list (`.events`) |
| `HttpTraceSink(endpoint, ...)` | POSTs JSON to a remote endpoint (`fail_silently=True` by default) |
| `TraceStoreSink(store)` | wraps a `TraceStore` |

Configure them globally:

```python
from aisuite import tracing

tracing.configure(tracing.LocalTraceSink(".aisuite/events.jsonl"))
```

Or pass per-run via `Runner.run_sync(..., trace_sinks=[...])`. Disable entirely with `tracing_disabled=True`.

## Stores

A `TraceStore` persists event records and reconstructs runs from them:

- **`JsonlTraceStore(path=".aisuite/events.jsonl")`** — appends JSON records line by line.
- **`InMemoryTraceStore()`** — keeps records in a list.

`reconstruct_runs(records)` groups events by `trace_id`, merges their fields, and computes per-run counts (events, messages, steps) and status. This is what the viewer reads.

## Writing a run's trace directly

A `RunResult` can serialize its own trace without any sink configured:

```python
result = Runner.run_sync(agent, "...")
result.write_trace_jsonl(".aisuite/runs.jsonl")   # append this run
result.print_trace()                               # human-readable summary to stdout
```

## The viewer

`aisuite/tracing/viewer.py` runs a small local web server that serves a React UI (bundled at `aisuite/tracing/static/viewer/`, source in [`viewer-ui/`](../components/viewer-ui.md)). Launch it:

```bash
python -m aisuite.tracing.viewer --trace-file .aisuite/runs.jsonl --host 127.0.0.1 --port 8765
```

Or from Python:

```python
from aisuite.tracing.viewer import start_viewer
server = start_viewer(trace_file=".aisuite/runs.jsonl")
print(server.url)   # http://127.0.0.1:8765
# ... later ...
server.stop()
```

The server exposes a JSON API the UI consumes:

| Endpoint | Returns |
|----------|---------|
| `GET /api/runs` | run summaries |
| `GET /api/runs/{trace_id}` | one run in detail |
| `GET /api/events/{trace_id}` | raw events for a run |
| `GET /api/artifacts/{artifact_id}` | artifact content (needs an artifact store) |
| `POST /api/import-jsonl` | import a JSONL trace file |

Pass `artifact_root=` (or an `artifact_store=`) to `start_viewer` so the viewer can load full artifact content referenced by dehydrated messages.

## What the viewer shows

The UI lists runs with search and a status filter (all/completed/running/failed). Selecting a run shows a stats strip (duration, tokens, tool count, approvals, errors, model) and three tabs: **Timeline** (filterable by Model/Tools/Approvals/Errors/Subagents, with expandable tool arguments and results), **Transcript** (every message), and **Raw JSON**. Subagent calls are clickable to drill into child runs. An embed mode (`?embed=1&trace_id=...`) gives a focused view for notebooks and reports.

## Related

- [The Agents API](agents-api.md) — where tracing context is established.
- [State & artifacts](state-and-artifacts.md) — how the viewer resolves artifact references.
- [Guide: view traces](../guides/view-traces.md).
- [viewer-ui component](../components/viewer-ui.md) — the UI source.
- [reference/tracing.md](../reference/tracing.md) — `TraceEvent`, sinks, and the viewer API in full.
