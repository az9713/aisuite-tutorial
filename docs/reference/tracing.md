# Reference: Tracing

`TraceEvent`, sinks, stores, and the viewer. Import from `aisuite.tracing`.

## TraceEvent

| Field | Type | Description |
|-------|------|-------------|
| `event_type` | TraceEventType | One of the event types below. |
| `trace_id` | str | Run identity. |
| `agent_name` | str | Emitting agent. |
| `event_id` | str | Auto-generated. |
| `timestamp` | str | Auto-generated. |
| `span_id` / `parent_span_id` | str \| None | Span nesting. |
| `parent_run_id` | str \| None | Parent run (subagents). |
| `group_id` | str \| None | Run grouping. |
| `run_name` | str \| None | Human-readable name. |
| `tags` | list[str] | Labels. |
| `metadata` | dict | Run metadata. |
| `data` | dict | Event-specific payload. |

### Event types

| Group | Types |
|-------|-------|
| Run | `run.started`, `run.completed`, `run.failed` |
| Model | `model.send`, `model.response`, `model.error` |
| Tool | `tool.allowed`, `tool.denied`, `tool.started`, `tool.completed`, `tool.failed` |

Schema version constant: `TRACE_SCHEMA_VERSION = "2026-05-15"`.

## Sinks

A sink implements `emit(event: TraceEvent) -> None`.

| Sink | Constructor | Destination |
|------|-------------|-------------|
| `LocalTraceSink` | `(path=".aisuite/events.jsonl")` | JSONL file (via `JsonlTraceStore`). |
| `InMemoryTraceSink` | `()` | `.events` list. |
| `HttpTraceSink` | `(endpoint, *, timeout=2.0, headers=None, fail_silently=True)` | POST JSON to `endpoint`. |
| `TraceStoreSink` | `(store: TraceStore)` | Wraps a store. |

### Global configuration

| Function | Description |
|----------|-------------|
| `configure(*sinks)` | Set the global sink list. |
| `get_configured_sinks() -> list[TraceSink]` | Current sinks. |
| `emit_event(sinks, event)` | Emit to all sinks. |

Per-run override: `Runner.run_sync(..., trace_sinks=[...])`; disable with `tracing_disabled=True`.

## Stores

A `TraceStore` persists records and reconstructs runs. Protocol: `append_event`, `append_events`, `append_record`, `append_records`, `import_jsonl`, `list_records`, `list_runs`, `get_run`, `list_events`.

| Store | Constructor | Backing |
|-------|-------------|---------|
| `JsonlTraceStore` | `(path=".aisuite/events.jsonl")` | append-only JSONL |
| `InMemoryTraceStore` | `(records=None)` | a list |

`reconstruct_runs(records)` groups events by `trace_id` and computes per-run `event_count`, `message_count`, `step_count`, and `status`.

## Normalization

| Function | Returns |
|----------|---------|
| `normalize_model_input(messages, *, model, preview_chars=200)` | `{model, input: {message_count, modalities, items}}` |
| `normalize_model_response(response, *, model, preview_chars=200)` | `{model, response: {kind, modalities, text_preview, finish_reason, tool_calls, ...}, usage: {...}}` |
| `normalize_usage(usage)` | normalized token counts plus `provider_raw` |

`kind` is `text` / `tool_calls` / `mixed` / `empty`; modalities include `text`, `image`, `tool_call`.

## Viewer

### From the CLI

```bash
python -m aisuite.tracing.viewer --trace-file .aisuite/runs.jsonl --host 127.0.0.1 --port 8765
```

### From Python

```python
start_viewer(trace_file=".aisuite/runs.jsonl", host="127.0.0.1", port=8765,
             ui_dist=None, artifact_store=None, artifact_root=None,
             trace_store=None) -> ViewerServer
```

Returns a started `ViewerServer`. `ViewerServer`: property `url`, methods `start()` and `stop()`. If `artifact_root` is given without `artifact_store`, a `FileArtifactStore` is created automatically.

### HTTP API

| Endpoint | Returns |
|----------|---------|
| `GET /api/runs` | `{runs: [...]}` |
| `GET /api/runs/{trace_id}` | `{run: {...}}` |
| `GET /api/events/{trace_id}` | `{events: [...]}` |
| `GET /api/artifacts/{artifact_id}` | artifact bytes (needs an artifact store) |
| `POST /api/import-jsonl` | `{imported: n, runs: [...]}` |
| `POST /api/events` | add a single event record |
| `GET /`, `GET /index.html` | the bundled UI |

UI assets are served from `aisuite/tracing/static/viewer/` (or `viewer-ui/dist/` in a source checkout).

## RunResult trace helpers

`RunResult` can serialize its own trace without sinks: `trace_to_dict()`, `write_trace_jsonl(path)`, `print_trace(file=None)`.

## Related

- [Tracing concept](../concepts/tracing.md)
- [Guide: view traces](../guides/view-traces.md)
- [viewer-ui component](../components/viewer-ui.md)
