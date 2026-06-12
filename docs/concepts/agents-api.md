# The Agents API

The Agents API is the higher-level layer for longer-running, structured work. You declare an `Agent` once and execute it with the `Runner`, which drives the tool loop and wires in policies, state, artifacts, and tracing.

## What it is

Two core types:

- **`Agent`** — a declarative, stateless definition of *what* to run.
- **`Runner`** — the executor that runs an agent to completion and returns a `RunResult`.

The Runner builds on the Chat Completions API: under the hood it calls `client.chat.completions.create(..., max_turns=...)` with the agent's tools, inside a trace context.

## Declaring an agent

```python
import aisuite as ai
from aisuite import Agent, Runner

agent = Agent(
    name="repo-helper",
    model="anthropic:claude-sonnet-4-6",
    instructions="You are a careful repo assistant. Answer from the code.",
    tools=[*ai.toolkits.files(root="."), *ai.toolkits.git(root=".")],
)
```

`Agent` fields:

| Field | Type | Meaning |
|-------|------|---------|
| `name` | str | Identifier, used in traces and as a subagent tool name |
| `model` | str | A `provider:model` string |
| `instructions` | str? | System prompt |
| `tools` | list[Callable] | Tools and toolkit functions |
| `model_settings` | dict | Extra kwargs merged into each model call (e.g. `temperature`) |
| `tags` | list[str] | Free-form labels propagated to traces |
| `metadata` | dict | Free-form metadata propagated to traces |

An `Agent` holds no run state. The same instance can be run many times.

## Running an agent

```python
result = Runner.run_sync(agent, "What changed in the last commit? Summarize in 3 bullets.")
print(result.final_output)
```

`Runner.run(...)` is the async form; `Runner.run_sync(...)` is synchronous (the async form delegates to it). Key parameters:

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `agent` | — | The agent to run |
| `input` | — | A string, a message list, or a `RunState` to resume |
| `client` | new `Client()` | The LLM client to use |
| `max_turns` | 5 | Tool-loop cap |
| `tool_policy` | none | Gate which tool calls run (see [tool policies](tool-policies.md)) |
| `state_store` + `thread_id` | none | Persist the thread (see [state & artifacts](state-and-artifacts.md)) |
| `artifact_store` | none | Offload large message payloads |
| `trace_sinks` / `tracing_disabled` | configured sinks | Observability (see [tracing](tracing.md)) |
| `run_name`, `group_id`, `parent_run_id`, `tags`, `metadata` | none | Trace identity and grouping |

Extra `**kwargs` merge into `agent.model_settings` for the underlying model call.

## The execution loop

`Runner.run_sync` does roughly this:

1. **Resolve input.** A `RunState` resumes a thread (its messages and metadata are restored); a string or list starts fresh. Artifact-dehydrated message fields are hydrated back to full content.
2. **Prepare the request.** Merge `model_settings` with kwargs; if the agent has tools, include them and set `max_turns`; if a `tool_policy` is given, build a `ToolPolicyContext`.
3. **Open a trace context.** Set the active run context (client, `trace_id`, agent name, sinks, policy, artifact store) so nested model and subagent calls inherit it. Emit `run.started`.
4. **Call the model** via `client.chat.completions.create(...)`, which runs the tool loop. On error, emit `run.failed` and re-raise.
5. **Assemble the result.** Extract all messages, build the `steps` list (agent → model response → tool calls/results), construct the `RunResult`, emit tool events if not already emitted, then `run.completed`.
6. **Persist (optional).** If `state_store` is set, convert to `RunState`, dehydrate large fields into the artifact store, and save under `thread_id`.

## What a run returns

`RunResult` carries the full outcome:

```python
result.final_output    # the agent's last text output
result.status          # "completed" | "requires_input" | "max_turns_exceeded" | "failed"
result.messages        # the complete message history
result.steps           # ordered RunStep list (typed: agent, model_response, tool_call, ...)
result.raw_responses   # raw provider responses
result.trace_id        # open this run in the viewer
result.to_state()      # convert to a persistable RunState
```

`RunResult` also has trace helpers: `trace_to_dict()`, `write_trace_jsonl(path)`, and `print_trace()`.

## Continuing a conversation

Two ways to resume:

**In-memory** — pass the previous `RunResult`:

```python
result = Runner.continue_sync(result, "Now also check the tests.")
```

**Persisted** — pass the agent plus a state store and thread id; the stored thread is loaded, your input appended, and the result saved back with optimistic-concurrency checking:

```python
result = Runner.continue_sync(
    agent, "Now also check the tests.",
    state_store=store, thread_id="repo-chat",
)
```

If no thread exists for that id, `continue_sync` raises `StateNotFoundError`. See [state & artifacts](state-and-artifacts.md).

## Subagents

An `Agent` can be exposed as a tool to another agent with `agent_tool(...)`:

```python
from aisuite import agent_tool

researcher = Agent(name="researcher", model="openai:gpt-4o", tools=[...])
lead = Agent(name="lead", model="anthropic:claude-sonnet-4-6",
             tools=[agent_tool(researcher)])
```

When the lead calls the researcher tool, the subagent runs with the parent's client, trace, group, policy, and stores inherited through the active run context — so the whole nested run shows up as one connected trace.

## Statuses and approval pauses

A run can end `requires_input` — for instance when a tool policy needs a human decision. The pattern is: inspect `result.status`, gather the human's answer, and resume with `continue_sync`. [Tool policies](tool-policies.md) covers approval flows end to end.

## Related

- [Tool calling](tool-calling.md) — the loop the Runner drives.
- [Tool policies](tool-policies.md), [State & artifacts](state-and-artifacts.md), [Tracing](tracing.md) — the production pieces.
- [reference/agents-api.md](../reference/agents-api.md) — full signatures.
