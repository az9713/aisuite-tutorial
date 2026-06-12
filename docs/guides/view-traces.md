# View traces

Record what an agent did and inspect it in a local web viewer — model calls, tool executions, approvals, errors, and artifacts, on a timeline.

**When you need this:** debugging why an agent did something, auditing approvals, or sharing a run.

## Prerequisites

- aisuite installed. The viewer ships bundled — no separate install.

## Steps

### 1. Record a trace

The simplest path: write a run's trace to a JSONL file.

```python
from aisuite import Agent, Runner
import aisuite as ai

agent = Agent(name="repo-helper", model="anthropic:claude-sonnet-4-6",
              tools=[*ai.toolkits.git(root=".")])

result = Runner.run_sync(agent, "What changed in the last commit?")
result.write_trace_jsonl(".aisuite/runs.jsonl")
```

Every `Runner.run` traces automatically; `write_trace_jsonl` appends the finished run to a file the viewer reads. To stream events live instead, configure a sink once:

```python
from aisuite import tracing
tracing.configure(tracing.LocalTraceSink(".aisuite/events.jsonl"))
```

### 2. Launch the viewer

From the command line:

```bash
python -m aisuite.tracing.viewer --trace-file .aisuite/runs.jsonl --host 127.0.0.1 --port 8765
```

Or from Python:

```python
from aisuite.tracing.viewer import start_viewer
server = start_viewer(trace_file=".aisuite/runs.jsonl")
print(server.url)        # http://127.0.0.1:8765
```

Open the printed URL in a browser.

### 3. (Optional) show artifact contents

If your runs use an artifact store, point the viewer at its root so it can load full payloads referenced by dehydrated messages:

```python
server = start_viewer(trace_file=".aisuite/runs.jsonl",
                      artifact_root=".aisuite/artifacts")
```

### 4. Read the run

The UI lists runs with search and a status filter. Open one to see:

- **Stats strip** — duration, tokens, tool count, approvals, errors, model.
- **Timeline** — every event, filterable by Model / Tools / Approvals / Errors / Subagents. Expand a tool call to see its arguments and result (stdout/stderr for shell). Click a subagent to drill into its child run.
- **Transcript** — the full message history.
- **Raw JSON** — the complete dump.

## Embedding a single run

For a notebook or report, the embed mode renders one run's detail view:

```
http://127.0.0.1:8765/?embed=1&trace_id=<the-trace-id>
```

`result.trace_id` gives you the id.

## Verification

After launching, `GET http://127.0.0.1:8765/api/runs` (or just load the page) should list your run. If the list is empty, the trace file path is wrong or no run has been written yet.

## Troubleshooting

**Empty run list** — the `--trace-file` doesn't exist or has no runs. Confirm `write_trace_jsonl` (or your sink) wrote to the same path you launched with.

**Port already in use** — pass a different `--port`.

**Artifacts show "preview only" / won't load** — the viewer has no artifact store. Pass `artifact_root=` (or `artifact_store=`) to `start_viewer`.

**Stopping the server** — `server.stop()` from Python, or Ctrl-C for the CLI.

## Related

- [Tracing concept](../concepts/tracing.md) — events, sinks, stores, identity.
- [viewer-ui component](../components/viewer-ui.md) — the UI source and how to build it.
- [reference/tracing.md](../reference/tracing.md) — the viewer's HTTP API.
