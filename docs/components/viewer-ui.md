# viewer-ui (trace viewer)

The React web UI for inspecting aisuite traces — runs, timelines, transcripts, tool calls, approvals, and artifacts. Source: [`viewer-ui/`](https://github.com/andrewyng/aisuite/tree/main/viewer-ui).

## What it is

A single-page app that renders the data served by aisuite's trace [viewer server](../reference/tracing.md#viewer) (`aisuite/tracing/viewer.py`). The built output is bundled into the Python package at `aisuite/tracing/static/viewer/`, so end users get the viewer without ever building it. `viewer-ui/` is the source you edit to change the UI.

## Tech stack

| Layer | Technology |
|-------|-----------|
| Framework | React 19 |
| Build | Vite 7 |
| Styling | Tailwind CSS 3 + PostCSS |
| Icons | lucide-react |
| Language | TypeScript / JSX |

## What it shows

- **Sidebar** — the run list, with text search and a status filter (all / completed / running / failed).
- **Detail panel** — a hero (title, status, trace id), a stats strip (duration, tokens, tool count, approvals, errors, model), and three tabs:
  - **Timeline** — every event, filterable by Model / Tools / Approvals / Errors / Subagents. Tool calls expand to show arguments and results (stdout/stderr for shell). Subagent calls are clickable to open the child run.
  - **Transcript** — the full message history.
  - **Raw JSON** — the complete run dump.
- **Embed mode** — `?embed=1&trace_id=<id>` renders just one run's detail, for notebooks and reports.
- **Theme** — dark/light toggle, persisted to `localStorage` (`aisuite-viewer-theme`).

It polls the server roughly every 1.5 s, so runs appear live as they execute.

## API it consumes

Served by the viewer server (see [reference/tracing.md](../reference/tracing.md#http-api)):

| Endpoint | Used for |
|----------|----------|
| `GET /api/runs` | the run list |
| `GET /api/runs/{traceId}` | run detail |
| `GET /api/artifacts/{artifactId}` | artifact content |
| `POST /api/import-jsonl` | importing a trace file |

The base URL is configurable via `VITE_API_BASE_URL` (defaults to same-origin).

## Build and run

```bash
cd viewer-ui
npm install
npm run dev       # Vite dev server → http://localhost:5173 (talks to a running viewer server)
npm run build     # production build → dist/
npm run preview   # preview the production build
```

After `npm run build`, the contents of `dist/` are what get bundled into `aisuite/tracing/static/viewer/` for distribution.

## How users actually open it

Most users never run `viewer-ui` directly — they launch the bundled viewer from Python or the CLI:

```bash
python -m aisuite.tracing.viewer --trace-file .aisuite/runs.jsonl
```

See [Guide: view traces](../guides/view-traces.md).

## Related

- [Tracing concept](../concepts/tracing.md) — what the events mean.
- [reference/tracing.md](../reference/tracing.md) — the server API the UI consumes.
- [OpenCoworker](opencoworker.md) — embeds the same viewer.
