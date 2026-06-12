# Reference: Policies, state stores, and artifact stores

The governance and persistence primitives. Import from `aisuite`.

## Tool policies

A policy implements `evaluate(context: ToolPolicyContext) -> bool | ToolPolicyDecision`.

### Built-ins

| Policy | Constructor | Behavior |
|--------|-------------|----------|
| `AllowAllToolPolicy` | `()` | Always `allowed=True`. |
| `DenyAllToolPolicy` | `(reason=None)` | Always `allowed=False` with `reason`. |
| `AllowToolsPolicy` | `(allowed_tools: list[str], reason=None)` | `allowed` iff `tool_name` is in the allowlist. |
| `RequireApprovalPolicy` | `(callback)` | Calls `callback(context) -> bool \| ToolPolicyDecision`. A bool becomes a decision with reason `"approved"`/`"denied"`. Any other return type → `TypeError`. |

### ToolPolicyContext

| Field | Type | Description |
|-------|------|-------------|
| `agent_name` | str | Agent making the call. |
| `tool_name` | str | Tool being called. |
| `arguments` | dict | The call's arguments. |
| `run_name`, `trace_id`, `group_id`, `parent_run_id` | str \| None | Run identity. |
| `tags` | list[str] | Run tags. |
| `metadata` | dict | Run metadata. |
| `messages` | list[dict] | Conversation so far (deep-copied). |
| `tool_metadata` | ToolMetadata \| None | The tool's declared metadata. |

### ToolPolicyDecision

| Field | Type | Default |
|-------|------|---------|
| `allowed` | bool | — |
| `reason` | str \| None | None |
| `metadata` | dict | `{}` |

### ToolMetadata and the @tool decorator

```python
@tool(metadata=ToolMetadata(...))
def my_tool(...): ...
```

| `ToolMetadata` field | Type | Default |
|----------------------|------|---------|
| `name` | str \| None | the function's `__name__` |
| `category` | str \| None | None |
| `risk_level` | `"low"` \| `"medium"` \| `"high"` | `"low"` |
| `capabilities` | list[str] | `[]` |
| `requires_approval` | bool | False |
| `description` | str \| None | None |
| `metadata` | dict | `{}` |

`@tool` attaches the metadata to the function (read by policies via `context.tool_metadata`).

## State stores

All implement the `StateStore` protocol:

```python
save_state(thread_id, state, *, revision=None, metadata=None) -> StoredRunState
load_state(thread_id) -> Optional[StoredRunState]
delete_state(thread_id) -> None
```

### StoredRunState

| Field | Type | Description |
|-------|------|-------------|
| `thread_id` | str | Thread key. |
| `state` | RunState | The persisted state. |
| `revision` | int | Version, increments per save. |
| `created_at` / `updated_at` | str | Timestamps. |
| `metadata` | dict | Store-level metadata. |

### Implementations

| Store | Constructor | Backing |
|-------|-------------|---------|
| `InMemoryStateStore` | `()` | a dict |
| `FileStateStore` | `(root=".aisuite/state")` | JSON files, atomic writes; `thread_id` URL-quoted into the filename |
| `PostgresStateStore` | `(connection, *, create_schema=False)` or `.from_dsn(dsn, *, create_schema=False)` | PostgreSQL (tables `agent_thread_heads`, `agent_messages`, `agent_compactions`) |

`PostgresStateStore` extras (`pip install 'aisuite[postgres]'`) — beyond the protocol: `compact_state(...)`, `list_compactions(...)`, `get_thread_head(...)`. It deduplicates unchanged message prefixes across saves.

### Optimistic concurrency

`save_state(..., revision=expected)` raises `StateConflictError` if the store's current revision differs from `expected`. Saving without a `revision` creates or overwrites without the check.

### CompactionRecord (Postgres)

| Field | Type | Description |
|-------|------|-------------|
| `compaction_id` | str | Record id. |
| `thread_id` | str | Owning thread. |
| `source_message_ids` | list[str] | Messages summarized. |
| `summary_message_id` | str | The replacement message. |
| `summary_text` | str | The summary. |
| `reason`, `model` | str \| None | Why / which model. |
| `input_token_count`, `output_token_count` | int \| None | Token accounting. |
| `created_at` | str | Timestamp. |
| `metadata` | dict | Extra. |

## Artifact stores

All implement the `ArtifactStore` protocol:

```python
put(data: bytes | str, *, media_type, metadata=None) -> ArtifactRef
get(ref: ArtifactRef | str) -> Artifact
delete(ref: ArtifactRef | str) -> None
```

### ArtifactRef

| Field | Type | Description |
|-------|------|-------------|
| `artifact_id` | str | Identifier. |
| `uri` | str | `memory://<id>` or `artifact://<id>`. |
| `media_type` | str | MIME type. |
| `size_bytes` | int | Payload size. |
| `metadata` | dict | Extra. |

### Artifact

`ref: ArtifactRef`, `data: bytes`, `created_at: str`. `.text(encoding="utf-8")` decodes `data`.

### Implementations

| Store | Constructor | Backing |
|-------|-------------|---------|
| `InMemoryArtifactStore` | `()` | a dict; `memory://` URIs |
| `FileArtifactStore` | `(root=".aisuite/artifacts")` | per-artifact dir with `data` + `metadata.json`; `artifact://` URIs |

Large message fields (>~20,000 chars in `content`/`diff`/`stdout`/`stderr`) are dehydrated into the store on save and hydrated before model calls. `get` on a missing file-store artifact raises `KeyError`.

## Related

- [Tool policies concept](../concepts/tool-policies.md)
- [State & artifacts concept](../concepts/state-and-artifacts.md)
- [reference/agents-api.md](agents-api.md)
