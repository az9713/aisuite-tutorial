# ADR 0004: Local-first tracing with a bundled viewer

**Status:** Accepted

## Context

Agent runs are hard to debug without visibility into each model call, tool execution, and approval. aisuite needed observability. The question was what shape it should take — and crucially, what it should *require*.

Constraints:
- aisuite has no backend and OpenCoworker explicitly runs with no server; keys and data stay on the user's machine. Tracing must not break that promise.
- Developers want to inspect a run immediately, in a notebook or a terminal, without standing up infrastructure.
- Production users still need to ship traces to a real collector.

## Decision

Make tracing **local-first**: events are emitted to local sinks (`LocalTraceSink` → JSONL, `InMemoryTraceSink`) by default, persisted in a local store (`JsonlTraceStore`/`InMemoryTraceStore`), and inspected with a **bundled local viewer** (`aisuite/tracing/viewer.py`, serving the pre-built `viewer-ui`). No external service is required to get full observability. For production, an `HttpTraceSink` ships the same events to a remote endpoint, and sinks are pluggable.

## Alternatives considered

### Option A: Require an external tracing backend (OTel collector, SaaS)
Emit to a remote service by default.
- **Pros:** production-grade aggregation out of the box.
- **Cons:** breaks the no-backend, data-stays-local promise; nothing works offline; heavyweight for "why did my agent do that?"

### Option B: Logs only, no viewer
Structured logs the user greps.
- **Pros:** trivial.
- **Cons:** agent runs are trees (subagents, tool calls); flat logs don't convey timelines, approvals, or artifacts well.

### Option C: Local-first with pluggable sinks and a bundled viewer (chosen)

## Rationale

Local-first keeps the privacy guarantee intact: by default, traces never leave the machine, matching how OpenCoworker already operates. A bundled viewer means a developer can go from "I have a trace file" to "I'm reading a timeline" with one command and zero setup — the UI is shipped inside the package at `tracing/static/viewer/`. Making sinks pluggable (and shipping `HttpTraceSink`) means production users aren't boxed in: the same events that render locally can be forwarded to a collector. The event model carries `trace_id`/`group_id`/`parent_run_id`, so subagent trees reconstruct correctly in any sink.

## Trade-offs

- The bundled viewer is a single-node tool; it isn't a multi-tenant, long-retention observability platform. Teams that need that wire up `HttpTraceSink` to their own stack.
- Shipping built UI assets inside the Python package adds weight and a build step (`viewer-ui` → `tracing/static/viewer/`).
- JSONL files grow unbounded unless rotated; long-running local sessions accumulate trace data under `.aisuite/`.

## Consequences

- Observability works offline and by default, with no infrastructure — see [view traces](../../guides/view-traces.md).
- Production observability is opt-in via a sink swap, not a re-architecture.
- The viewer is reusable beyond OpenCoworker: the CLI and any aisuite app get the same UI for free. See [viewer-ui](../../components/viewer-ui.md).
