# How persistent memory works in research-desk

research-desk "remembers" your conversation across restarts: quit the app, run it again,
ask *"what did I just ask you about?"*, and it answers correctly. This doc explains exactly
how that works — what is stored, where, when it is written, and what kind of memory it is
(and is not).

The whole feature is built on one aisuite primitive: a **state store**. research-desk uses
[`FileStateStore`](../../aisuite/agents/state_store.py); the same code path also supports
in-memory and Postgres stores.

---

## 1. What "memory" means here: conversation replay, not facts

There are two very different things people call "memory":

| | research-desk uses this | (not this) |
|---|---|---|
| **Conversation memory** | ✅ store the *entire message thread* and replay it to the model every turn | |
| **Semantic / fact memory** | | ❌ store discrete facts and retrieve the relevant ones by meaning |

research-desk has **conversation memory**. It does not summarise or index anything. When
you resume, it loads every prior message (system, user, assistant, tool results) and sends
the whole transcript to the model again. The model "remembers" simply because it re-reads
the full conversation on each turn.

> This is the same distinction as between research-desk and OpenCoworker: OpenCoworker's
> `platform/coworker/memory/` is a SQLite *fact* store (durable notes injected into the
> prompt). research-desk's `FileStateStore` is *thread* memory (verbatim replay). Different
> problems, different mechanisms.

---

## 2. The moving parts

| Piece | What it is | File |
|-------|-----------|------|
| `FileStateStore` | reads/writes thread state as JSON files | `aisuite/agents/state_store.py` |
| `RunState` | one thread's data: messages, steps, metadata, status | `aisuite/agents/types.py` |
| `StoredRunState` | a `RunState` plus bookkeeping: `revision`, timestamps | `aisuite/agents/state_store.py` |
| `thread_id` | the key that identifies one conversation | set in `desk.py` |
| `Runner.run_sync` / `continue_sync` | start a thread / resume a thread | `aisuite/agents/runner.py` |

In `desk.py` the wiring is tiny:

```python
STATE_DIR = HERE / ".aisuite" / "state"
THREAD_ID = "research-desk"
store = ai.FileStateStore(root=str(STATE_DIR))
```

One fixed `thread_id` means research-desk keeps **one** ongoing conversation. (Use a
different `thread_id` per conversation and you would get multiple independent memories.)

---

## 3. The lifecycle: new vs. resume

At startup, `desk.py` asks the store whether this thread already exists:

```python
stored = store.load_state(THREAD_ID)
if stored:                                   # ── RESUME ──
    model = stored.state.metadata.get("model", "openai:gpt-4o-mini")
    is_new = False
else:                                         # ── NEW ──
    model = pick_model()
    is_new = True
```

Then each turn routes to one of two `Runner` methods:

```python
if is_new:
    result = ai.Runner.run_sync(
        agent, prompt,
        state_store=store, thread_id=THREAD_ID,
        metadata={"model": model},            # remember the model (see §6)
    )
    is_new = False
else:
    result = ai.Runner.continue_sync(
        agent, prompt,
        state_store=store, thread_id=THREAD_ID,
    )
```

- **`run_sync`** starts a fresh thread. It first checks the store, and if the thread already
  exists it raises `ThreadAlreadyExistsError` — a guard against silently clobbering a saved
  conversation. So `run_sync` is used **exactly once** per thread (the first message of a
  brand-new conversation).
- **`continue_sync`** is used for every later message *and* for every message after a resume.
  It loads the saved state, appends your new message, runs, and saves again.

```
                 ┌──────────────────────────────┐
   fresh start → │ run_sync(state_store, thread) │ → save revision 1
                 └──────────────────────────────┘
                 ┌──────────────────────────────┐
   every other → │ continue_sync(...)           │ → load → append → run → save +1
   message       └──────────────────────────────┘
```

`--reset` simply deletes the file:

```python
store.delete_state(THREAD_ID)    # unlinks research-desk.json
```

---

## 4. Anatomy of the saved file

The state lives at `projects/research-desk/.aisuite/state/research-desk.json`
(the filename is the URL-quoted `thread_id`). A real one after four turns:

```jsonc
{
  "schema_version": 1,
  "thread_id": "research-desk",
  "revision": 4,                       // bumped on every save (see §5)
  "created_at": "…", "updated_at": "…",
  "metadata": {},
  "state": {
    "agent_name": "desk",
    "status": "completed",
    "max_turns": 12,
    "metadata": { "model": "openai:gpt-4o-mini" },   // the remembered model (§6)
    "messages": [ /* the whole transcript — see below */ ],
    "steps":    [ /* 28 trace steps, cumulative (see ORCHESTRATION.md) */ ],
    "trace_id": "…", "run_name": null, "parent_run_id": null,
    "group_id": null, "tags": []
  }
}
```

The `messages` array is the memory. After four turns it held 21 messages, and the role
sequence tells the whole story of the conversation:

```
system                                          ← the lead's instructions
user, assistant, tool, assistant, tool,         ┐
  tool, tool, tool, tool, tool, assistant,      │ TURN 1: "explain big bang"
  tool, assistant, tool, assistant              ┘  (the planner/researcher/critic/writer
                                                     calls show up as tool messages)
user, assistant                                 ← TURN 2: "what did I just ask?" (no tools)
user, assistant                                 ← TURN 3
user, assistant                                 ← TURN 4
```

Notice turn 1 is fat with `tool` messages (the team ran), while turns 2–4 are bare
`user`/`assistant` pairs (answered straight from this transcript, no tools). That is the
same accumulation described in [`ORCHESTRATION.md`](ORCHESTRATION.md) — `messages` and
`steps` both grow with every turn and are replayed in full.

---

## 5. How a save actually happens — revisions and atomic writes

`FileStateStore.save_state` (in `state_store.py`) does three things:

```python
current = self.load_state(thread_id)                 # 1. read current
_assert_revision(thread_id, current.revision, revision)  # 2. concurrency check
stored = _next_stored_state(...)                     #    revision += 1, keep created_at
self._write_stored_state(stored)                     # 3. atomic write
```

**Revisions = optimistic concurrency.** Each save increments `revision`. `continue_sync`
passes the revision it loaded; if some *other* writer had bumped the file in between, the
check fails with `StateConflictError` instead of overwriting their work. In the single-user
CLI this never trips — but it is why the same store works safely under a multi-process
server.

**Atomic writes = crash safety.** The write is never done in place:

```python
tmp_path = path.with_name(f".{path.name}.{new_id('tmp')}.tmp")
tmp_path.write_text(json.dumps(stored.to_dict(), sort_keys=True))
os.replace(tmp_path, path)         # atomic rename on POSIX and Windows
```

If the process dies mid-write, the original `research-desk.json` is untouched — you never
get a half-written, corrupt memory file.

**Artifact dehydration.** Before saving, `run_sync` calls
`dehydrate_messages(state.messages, artifact_store)`. With an artifact store, large payloads
(big tool outputs, images) are swapped for lightweight references so the JSON stays compact,
and rehydrated on load. research-desk passes no artifact store, so this is a pass-through —
but it is the hook you would add if a tool started returning megabytes.

---

## 6. Remembering the *model* (a neat reuse of `metadata`)

The provider/model you pick at startup also needs to survive a restart — otherwise resume
would have to ask again. research-desk stashes it in the run's `metadata`:

```python
ai.Runner.run_sync(..., metadata={"model": model})
```

`metadata` is part of `RunState`, so it is persisted alongside the messages. On the next
launch:

```python
model = stored.state.metadata.get("model", "openai:gpt-4o-mini")
```

So a single field does double duty: it travels with the trace *and* serves as the app's
"remember my last choice" setting. No separate config file needed.

---

## 7. Scaling characteristics (and the limits of this approach)

| Concern | Behavior in research-desk |
|---------|---------------------------|
| **Context growth** | The **entire** transcript is replayed every turn. Tokens-per-turn grow without bound as the conversation gets longer — eventually you hit the model's context window. |
| **Compaction** | `FileStateStore` does **not** summarise old messages. `PostgresStateStore` does (it rolls old ranges into `CompactionRecord`s) — that is the upgrade path for long-lived threads. |
| **Concurrency** | Single file, optimistic `revision` check. Fine for one CLI user; the Postgres store is the multi-process option. |
| **Durability** | Atomic temp-file rename; survives a crash mid-write. |
| **Privacy** | The file holds your full conversation, so `projects/research-desk/.gitignore` excludes `.aisuite/` — memory is never committed. |

The practical takeaway: this is the right design for a personal, single-thread assistant.
For long or shared conversations you would switch the one line
`store = ai.FileStateStore(...)` to a `PostgresStateStore` and get compaction + multi-process
safety with no other code change — that is the point of the `StateStore` interface.

---

## 8. Source map

| Claim | File / symbol |
|-------|---------------|
| JSON read/write, atomic save, revisions | `aisuite/agents/state_store.py` — `FileStateStore`, `_assert_revision` |
| `ThreadAlreadyExistsError` guard on fresh start | `aisuite/agents/runner.py` — `run_sync` |
| load → append → run → save on resume | `aisuite/agents/runner.py` — `continue_sync` |
| messages/steps carried across turns | `runner.py` — the `RunState` branch (`prior_steps`) |
| what a thread stores | `aisuite/agents/types.py` — `RunState` |
| app wiring (thread_id, model metadata, reset) | [`desk.py`](desk.py) |

See also [`ORCHESTRATION.md`](ORCHESTRATION.md) for how those replayed `messages`/`steps`
produce the `[team]` and `[trace]` views.
