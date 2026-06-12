# State and artifacts

Two persistence mechanisms let agent runs outlive a single process: **state stores** persist a conversation thread so it can resume later, and **artifact stores** offload large payloads so they don't bloat the message history.

## State stores

A state store persists a `RunState` — the serializable snapshot of a thread — keyed by a `thread_id`.

### Creating and resuming a thread

```python
from aisuite import FileStateStore, Runner

store = FileStateStore(root=".aisuite/state")

# First turn: create the thread
result = Runner.run_sync(agent, "Start reviewing the codebase",
                         state_store=store, thread_id="review-1")

# Later, in a different process: resume it
result = Runner.continue_sync(agent, "Now check the tests",
                              state_store=store, thread_id="review-1")
```

`Runner.run_sync` with a `state_store` + `thread_id` creates the thread and saves the resulting `RunState`. `continue_sync` loads the stored state, appends your input, runs, and saves the new state back.

> **Note:** `state_store` and `thread_id` must be provided together. Creating a thread id that already exists raises `ThreadAlreadyExistsError` — use `continue_sync` to resume instead. Resuming a non-existent thread raises `StateNotFoundError`.

### Implementations

| Store | Backing | Use when |
|-------|---------|----------|
| `InMemoryStateStore()` | a dict | tests, single-process sessions |
| `FileStateStore(root=".aisuite/state")` | JSON files (atomic writes) | local apps, the CLI |
| `PostgresStateStore(connection)` / `.from_dsn(dsn)` | PostgreSQL | multi-process, durable, concurrent |

All implement the `StateStore` protocol: `save_state(thread_id, state, *, revision=None)`, `load_state(thread_id)`, `delete_state(thread_id)`. Requires `pip install 'aisuite[postgres]'` for the Postgres store.

### Optimistic concurrency

Each stored thread carries a monotonically increasing `revision`. To save safely, pass the revision you loaded:

```python
stored = store.load_state(thread_id)        # revision == 5
# ... mutate ...
store.save_state(thread_id, state, revision=stored.revision)
# if another writer advanced it to 6 first → StateConflictError
```

`Runner.continue_sync` does this for you, so two workers resuming the same thread can't silently clobber each other — the loser gets `StateConflictError` and can retry with fresh state.

### What's in a RunState

`agent_name`, `messages`, `status`, `run_name`, identity/grouping fields (`trace_id`, `parent_run_id`, `group_id`), `tags`, `metadata`, `steps`, and `max_turns`. It serializes with `to_dict()` / `from_dict()` and must be JSON-serializable (non-serializable values raise `TypeError` on save).

### Compaction (Postgres)

The Postgres store supports **compaction**: summarizing a range of older messages into a single summary message to stay within the context window, recorded as a `CompactionRecord` (which source messages were replaced, the summary, the model used, and token counts). The store deduplicates unchanged message prefixes across saves, so resuming a long thread doesn't rewrite the whole history.

## Artifact stores

An artifact is a blob — bytes plus a media type — stored out-of-band and referenced from messages. They solve a specific problem: when a tool returns a 2 MB file or a giant diff, embedding it in every subsequent model call wastes tokens and context.

### Dehydration and hydration

When an `artifact_store` is attached to a run, aisuite **dehydrates** large message fields (long `content`, `diff`, `stdout`, `stderr` — over ~20,000 chars by default) before persisting: the full value is written to the artifact store and replaced in the message with a reference plus a short preview. Before the next model call, those fields are **hydrated** back to full content. The model sees complete data; the stored history stays compact.

### Implementations

| Store | Backing | Reference URI |
|-------|---------|---------------|
| `InMemoryArtifactStore()` | a dict | `memory://<id>` |
| `FileArtifactStore(root=".aisuite/artifacts")` | per-artifact directories (`data` + `metadata.json`) | `artifact://<id>` |

Both implement the `ArtifactStore` protocol: `put(data, *, media_type, metadata=None) -> ArtifactRef`, `get(ref) -> Artifact`, `delete(ref)`. An `Artifact` is `ref` + `data` (bytes); call `.text()` to decode. An `ArtifactRef` carries `artifact_id`, `uri`, `media_type`, `size_bytes`, and `metadata`.

### Using one

```python
from aisuite import FileArtifactStore, FileStateStore, Runner

result = Runner.run_sync(
    agent, "Read every file in src/ and summarize",
    state_store=FileStateStore(),
    thread_id="summarize-src",
    artifact_store=FileArtifactStore(),
)
```

The trace viewer can load an artifact's full content on demand from its reference, so a compact transcript still lets you inspect exactly what a tool produced.

## Related

- [The Agents API](agents-api.md) — where stores plug into a run.
- [Guide: persist and resume runs](../guides/persist-and-resume-runs.md).
- [reference/policies-and-stores.md](../reference/policies-and-stores.md) — full signatures and errors.
