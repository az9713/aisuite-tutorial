# Common issues

The errors you'll actually hit, ordered by how often they come up. Each: the symptom as you'd see it, the cause, and the exact fix.

## `ValueError: Invalid model format. Expected 'provider:model', got '...'`

**Cause:** The `model` argument has no colon. aisuite needs `provider:model`.

**Fix:** Add the provider prefix.

```python
client.chat.completions.create(model="openai:gpt-4o", ...)   # not "gpt-4o"
```

## `ValueError: Invalid provider key '...'. Supported providers: {...}`

**Cause:** The provider prefix doesn't match a discovered provider. Usually a typo, or a custom provider whose file isn't named correctly.

**Fix:** Use a key from the error's list (see [reference/providers.md](../reference/providers.md)). Remember AWS Bedrock is `aws`, not `aws-bedrock`. If you added a provider, confirm the file is `aisuite/providers/<key>_provider.py` with class `<Key>Provider`, and restart the process (`get_supported_providers()` is cached).

## `ImportError` / `ModuleNotFoundError` when a provider initializes

**Cause:** The provider's SDK isn't installed. The base package ships no provider SDKs.

**Fix:** Install the matching extra.

```shell
pip install 'aisuite[anthropic]'   # or [all]
```

See the extra for each provider in [reference/providers.md](../reference/providers.md).

## Authentication / 401 errors from a provider

**Cause:** The API key isn't set, or is set under the wrong variable.

**Fix:** Export the correct variable ([table here](../reference/configuration.md#environment-variables)) or pass it in code:

```python
client = ai.Client({"openai": {"api_key": "sk-..."}})
```

For AWS, Google, and WatsonX, multiple variables are required (region, project, service URL) — check the full set.

## `TypeError: ... is missing a type annotation` when passing a tool

**Cause:** A tool function has an unannotated parameter. aisuite builds the schema from annotations, so every parameter needs one.

**Fix:** Annotate all parameters.

```python
def get_price(ticker: str) -> str:   # not def get_price(ticker):
    ...
```

## The model ignores a tool / never calls it

**Cause:** The tool's description is too thin. The docstring summary and `Args:` section are the only signal the model has.

**Fix:** Write a specific docstring and tell the agent to use its tools in `instructions`. Verify by inspecting `result.steps` (or `response.choices[0].message.tool_calls`) for a `tool_call`.

## `ValueError: One or more tools is not callable`

**Cause:** Something in `tools` is neither a function nor an OpenAI-format spec — commonly a toolkit passed without spreading.

**Fix:** Spread toolkits with `*`, since each factory returns a *list*:

```python
tools=[*ai.toolkits.files(root="."), my_function]   # not [ai.toolkits.files(root=".")]
```

## `ImportError: MCP tools require the 'mcp' package`

**Cause:** You passed an MCP config (or used `MCPClient`) without the MCP extra.

**Fix:** `pip install 'aisuite[mcp]'`.

## An MCP server never starts (stdio)

**Cause:** `npx` isn't on PATH, or the server package name/args are wrong.

**Fix:** Run the exact command in your shell first:

```bash
npx -y @modelcontextprotocol/server-filesystem /docs
```

Once that works, the same `command`/`args` work in aisuite. Confirm Node.js is installed (`node --version`).

## `ThreadAlreadyExistsError`

**Cause:** You called `Runner.run_sync(..., thread_id=X)` for a thread that already exists. `run_sync` *creates*; it won't overwrite.

**Fix:** Resume with `continue_sync` instead.

```python
Runner.continue_sync(agent, "next message", state_store=store, thread_id="X")
```

## `StateNotFoundError`

**Cause:** `continue_sync` found no thread for that `thread_id`.

**Fix:** Check the id, and that you're using the same store and `root`/DSN. Create the thread first with `run_sync` if it's genuinely new.

## `StateConflictError`

**Cause:** Two writers saved the same thread; your save used a stale `revision`. This is the optimistic-concurrency guard working.

**Fix:** Reload, re-apply, and retry.

```python
stored = store.load_state(thread_id)
# re-apply your change to stored.state
store.save_state(thread_id, stored.state, revision=stored.revision)
```

## `TypeError: RunState contains values that are not JSON serializable`

**Cause:** A tool returned a non-serializable object (a custom class, a file handle) that ended up in the message history, which state stores must serialize.

**Fix:** Return JSON-friendly values from tools — strings, numbers, dicts, lists. Convert objects before returning.

## `TypeError: Approval callback must return a bool or ToolPolicyDecision`

**Cause:** A `RequireApprovalPolicy` callback returned something else (`None`, a string).

**Fix:** Return `True`/`False` or a `ToolPolicyDecision`.

## The trace viewer shows an empty run list

**Cause:** The `--trace-file` doesn't exist, has no runs yet, or differs from where runs were written.

**Fix:** Confirm a run was written to that exact path (`result.write_trace_jsonl(path)` or your configured sink), then relaunch pointing at it. If the port is busy, pass a different `--port`.

## Viewer shows artifacts as "preview only" and won't load full content

**Cause:** The viewer has no artifact store to resolve references.

**Fix:** Launch with an artifact root:

```python
start_viewer(trace_file=".aisuite/runs.jsonl", artifact_root=".aisuite/artifacts")
```

## OpenCoworker on Windows: SmartScreen blocks the installer

**Cause:** The build isn't Authenticode-signed yet.

**Fix:** Choose **More info → Run anyway**. See the [OpenCoworker quickstart](../opencoworker-quickstart.md).

## Still stuck?

- Re-read the relevant [concept](../concepts/) or [reference](../reference/) page — most errors map to one.
- Check the runnable [`examples/`](https://github.com/andrewyng/aisuite/tree/main/examples) for a working version of what you're doing.
- Ask in the project [Discord](https://discord.gg/T6Nvn8ExSb).
