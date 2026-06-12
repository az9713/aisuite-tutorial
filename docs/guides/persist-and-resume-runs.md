# Persist and resume runs

Save an agent conversation so it survives a restart, and pick it up later in another process — keyed by a `thread_id`.

**When you need this:** chat sessions that span requests, long tasks that resume after a crash, or any multi-process harness.

## Prerequisites

- An agent (see [give an agent tools](give-an-agent-tools.md)).
- For durable, concurrent storage: PostgreSQL and `pip install 'aisuite[postgres]'`.

## Steps

### 1. Choose a state store

| Store | Use when |
|-------|----------|
| `InMemoryStateStore()` | tests, a single process |
| `FileStateStore(root=".aisuite/state")` | local apps, one machine |
| `PostgresStateStore.from_dsn(dsn)` | multiple processes, durability, concurrency |

```python
from aisuite import FileStateStore
store = FileStateStore(root=".aisuite/state")
```

### 2. Create a thread on the first turn

Pass `state_store` and a `thread_id` to `run_sync`:

```python
from aisuite import Agent, Runner

agent = Agent(name="assistant", model="openai:gpt-4o",
              instructions="Help the user with their project.")

result = Runner.run_sync(
    agent, "Let's start reviewing the architecture.",
    state_store=store, thread_id="proj-42",
)
```

The resulting `RunState` is saved under `proj-42`.

### 3. Resume it later

In a different process — pass the agent, the same store, and the same `thread_id` to `continue_sync`:

```python
store = FileStateStore(root=".aisuite/state")   # same root
result = Runner.continue_sync(
    agent, "Now look at the data layer.",
    state_store=store, thread_id="proj-42",
)
```

`continue_sync` loads the stored thread, appends your input, runs, and saves the new state back — with optimistic-concurrency checking so a second writer can't clobber the first.

### 4. (Optional) offload large payloads

For agents that read big files or produce large diffs, attach an artifact store so message history stays compact:

```python
from aisuite import FileArtifactStore
result = Runner.run_sync(
    agent, "Summarize every file in src/",
    state_store=store, thread_id="proj-42",
    artifact_store=FileArtifactStore(),
)
```

Large fields are dehydrated into the artifact store on save and hydrated back before the next model call. See [state & artifacts](../concepts/state-and-artifacts.md).

## Using Postgres

```python
from aisuite import PostgresStateStore
store = PostgresStateStore.from_dsn(
    "postgresql://user:pass@localhost/aisuite", create_schema=True,
)
```

`create_schema=True` creates the tables on first use. The Postgres store also supports message-prefix deduplication and compaction for long threads.

## Verification

Confirm the thread round-trips:

```python
stored = store.load_state("proj-42")
print(stored.revision)                  # increments each save
print(len(stored.state.messages))       # grows across turns
```

## Troubleshooting

**`ThreadAlreadyExistsError`** — you called `run_sync` with a `thread_id` that already exists. Use `continue_sync` to resume an existing thread; `run_sync` is for creating one.

**`StateNotFoundError`** — `continue_sync` found no thread for that id. Check the `thread_id` and that you're pointing at the same store/root.

**`StateConflictError`** — another writer advanced the thread's revision before your save. Reload with `load_state`, re-apply, and retry. This is the concurrency guard working as intended.

**`TypeError: RunState contains values that are not JSON serializable`** — a tool returned a non-serializable object that ended up in the messages. Return JSON-friendly values (strings, numbers, dicts, lists) from tools.

## Related

- [State & artifacts concept](../concepts/state-and-artifacts.md) — stores, revisions, compaction.
- [The Agents API](../concepts/agents-api.md) — `run` vs `continue`.
- [reference/policies-and-stores.md](../reference/policies-and-stores.md) — full signatures and errors.
