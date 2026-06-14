# How the research-desk orchestration works — reading the trace

This doc explains, in detail, what these two trace views actually mean:

```
[team] planner -> researcher -> researcher -> researcher -> researcher -> researcher -> critic -> writer
```

```
[trace]
    - agent: desk
    - model_response: model_response
    - model_response: model_response
    - model_response: model_response
    - model_response: model_response
    - model_response: model_response
    - tool_call: planner (allowed=True)
    - tool_result: planner (status=success)
    - tool_call: researcher (allowed=True)
    - tool_result: researcher (status=success)
    ...
```

They come from the same data (`result.steps`); `[team]` is a one-line summary and
`[trace]` is the full list. To read either correctly you need three facts about how
aisuite runs a multi-agent turn. Each is explained below, then we walk the traces
line by line, then reconstruct what *actually* happened in time.

---

## 1. The cast: five agents, one of them the boss

`build_lead()` in [`desk.py`](desk.py) creates five `ai.Agent` objects:

| Agent | Role | Tools |
|-------|------|-------|
| `desk` | **lead / orchestrator** | the other four agents (as tools) |
| `planner` | break the request into steps | none |
| `researcher` | read the notes, return findings | `toolkits.files` (read) |
| `critic` | re-read the notes, verify findings | `toolkits.files` (read) |
| `writer` | turn findings into the final answer | none |

The lead's *only* tools are the other agents. That is the whole multi-agent trick,
and it relies on one function:

```python
tools=[
    ai.agent_tool(planner,    description="..."),
    ai.agent_tool(researcher, description="..."),
    ai.agent_tool(critic,     description="..."),
    ai.agent_tool(writer,     description="..."),
]
```

### `agent_tool` turns an agent into a callable tool

[`aisuite/agents/tools.py`](../../aisuite/agents/tools.py) wraps an `Agent` in a plain
function. When the lead "calls the researcher," it is really calling this:

```python
def run_subagent(input: str) -> str:
    result = Runner.run_sync(agent, input, client=..., parent_run_id=..., ...)
    return str(result.final_output)
```

So a sub-agent call is a **complete, separate `Runner.run_sync`** — its own model
round-trips, its own tool loop (the researcher reads files inside *its* run), its own
final output. The lead never sees the researcher's intermediate work; it only receives
the returned string. To the lead, `researcher` looks identical to any other tool: same
JSON schema, same call mechanism. There is no special "multi-agent framework" — it is
the ordinary tool-calling loop, one layer deep.

---

## 2. Orchestration is *soft*: the lead is an LLM in a loop, not a hard-coded pipeline

There is no Python `if/else` sequencing the four specialists. The order lives in the
lead's **instructions** (`desk.py`):

> 1. Call `planner` to break the request into steps.
> 2. Call `researcher` to gather findings from the notes.
> 3. Call `critic` to verify those findings.
> 4. Call `writer` to produce the final answer.
> Skip steps that don't apply.

At runtime the lead is driven by the Chat Completions **tool loop** in
[`aisuite/client.py`](../../aisuite/client.py) (`_tool_runner`):

```
loop (up to max_turns):
    response = model(messages)                 # the lead decides what to do next
    if response has no tool_calls:
        return response                        # this is the final answer
    results = execute_tool(response.tool_calls) # run planner / researcher / ...
    messages += [assistant turn, tool results]  # feed results back in
```

Each iteration is **one model call** by the lead. The model looks at the conversation
so far (including any tool results already returned) and chooses the next tool — or
decides it is done and emits plain text. So the planner→researcher→critic→writer order
is the model *following its instructions*, not a guarantee. On a different question the
lead may skip the planner, call the researcher twice, or answer with no tools at all.

> **Why `researcher` appears five times.** The lead chose to make five separate research
> passes before moving on. That is a model decision — it may split the work across passes,
> or simply over-call. Each of those five entries is a full researcher sub-run that opens
> and reads the (large) notes file. This is the main cost driver of the app, and it is
> visible precisely because the trace records every call. See *Implications* below.

---

## 3. The trace is **cumulative across the whole conversation**, not per-turn

This is the single most misread part of the output. Both `[team]` and `[trace]` iterate
`result.steps`, and `result.steps` carries **every prior turn's steps** forward.

When you resume a saved thread, [`runner.py`](../../aisuite/agents/runner.py) does:

```python
prior_steps = copy.deepcopy(input.steps)         # all steps from earlier turns
...
steps = [*prior_steps, agent_step, *model_response_steps, *tool_steps]
```

and `result.to_state()` saves that whole list back to the `FileStateStore`. So after
several turns the steps look like:

```
[ turn 1 steps ][ turn 2 steps ][ turn 3 steps ][ turn 4 steps ]
```

appended in order. Two consequences that explain everything you saw:

- **`agent: desk` appears once per turn in the thread.** Three `agent: desk` lines = the
  third turn of a resumed conversation (turns 1–3 each contributed one).
- **Every turn's `[team]` line shows the *same* `planner -> researcher×5 -> critic ->
  writer`.** Those eight tool calls happened on **turn 1 only**. Later turns (e.g. "what
  did I just ask?") answer straight from the conversation history with **no new tool
  calls** — but because the summary reads the *accumulated* steps, turn 1's chain is
  replayed on every subsequent `[team]` line. The later turns add only an `agent: desk`
  plus a `model_response`, with no tools.

In other words: the `[team]` line is a running tally of *every* sub-agent call made in the
thread so far, not "what this turn did."

---

## 4. Walking the `[trace]` step list

Within a single turn, `runner.py` assembles steps in a fixed shape — **not** in
chronological order:

```python
steps = [*prior_steps, agent_step, *model_response_steps, *tool_steps]
#         ^older turns   ^"agent"    ^ALL model calls       ^ALL tool calls
```

So for one turn you always see: the `agent` marker, then *every* model response grouped
together, then *every* tool call/result grouped together. The model calls and tool
executions actually **interleaved** in time (call → tools → call → tools …), but the
trace lists them in two blocks. Keep that in mind — the vertical order is a grouping,
not a timeline.

### Step types

| Step | Meaning | Built from |
|------|---------|-----------|
| `agent: desk` | start of one lead run (one user turn) | `agent_step` in `run_sync` |
| `model_response` | one model round-trip by the lead | `intermediate_responses` + final, via `_build_response_steps` |
| `tool_call: X (allowed=True)` | the lead invoked sub-agent X | `response.tool_events`, via `_build_tool_steps` |
| `tool_result: X (status=success)` | sub-agent X returned without error | same |

- **Five `model_response` before the first `tool_call`** does *not* mean "5 thinking steps
  then tools." It means turn 1's lead loop made **five model calls total**, and the runner
  lists them all before the tool block. Four of those calls each requested one or more
  tools; the fifth produced the final text answer (no tools → loop exits).
- **`allowed=True`** comes from the tool-policy layer. research-desk sets no policy, so
  everything is allowed — but each call is still recorded as `allowed=True` (the same hook
  the `aisuite-code` CLI uses to gate tools behind an approval prompt).
- **`status=success`** means the sub-agent run completed and returned a string. A sub-agent
  that raised would show `status` reflecting the failure (and, in aisuite, the exception
  propagates — there is no silent swallow).

### The trailing `agent: desk / model_response` pairs

```
    - tool_result: writer (status=success)   <- end of turn 1's tool block
    - agent: desk                            <- turn 2 begins
    - model_response: model_response         <- turn 2 answered from memory, no tools
    - agent: desk                            <- turn 3 begins
    - model_response: model_response         <- turn 3, again no tools
    ...
```

Each trailing `agent: desk` + `model_response` with **no tools** is a later turn that the
lead answered directly from conversation history (for example, "what did I just ask you
about?" → "You asked me to explain the Big Bang"). No planning, no notes, no team — just
the lead reading the thread and replying.

---

## 5. What actually happened, in time

Putting it together, here is the true chronology behind a trace that shows
`agent: desk ×4`, `model_response ×(5+3)`, and one block of 8 tools:

```
TURN 1  user: "explain big bang"          (fresh, used the full team)
  lead model call 1  -> requests planner
    planner sub-run  -> returns a step list
  lead model call 2  -> requests researcher (x1..2)
    researcher sub-run(s) -> read notes, return findings
  lead model call 3  -> requests researcher (more passes)
  lead model call 4  -> requests researcher, then critic, then writer
    critic sub-run   -> re-reads notes, verifies
    writer sub-run   -> drafts the final answer
  lead model call 5  -> emits final text (no tools) -> loop ends
  => steps: agent, model_response×5, [planner, researcher×5, critic, writer]
  => saved to FileStateStore as revision 1

TURN 2  user: "what did I just ask?"       (answered from memory)
  lead model call 1  -> plain text, no tools
  => steps appended: agent, model_response          (no tool block)
  => revision 2

TURN 3, TURN 4 ...                          (same: agent + model_response, no tools)
```

The exact split of the 8 tool calls across model calls 2–4 cannot be recovered from the
grouped trace — you can see *what* was called and *how many* model calls happened, but not
the precise round boundaries. (The chronological truth is available in the live trace-sink
events — `model.send`, `tool.allowed`, `tool.completed` — emitted in real order; the step
list is the post-hoc grouped summary.)

---

## 6. Implications

- **Cost scales with the tool calls, and the trace shows them.** Turn 1 made 5 lead model
  calls **plus** 8 sub-agent runs (each its own model call), and the researcher read a
  ~109 KB notes file five times. That is the bulk of the spend. If you want it cheaper, the
  lever is the lead prompt: tell it to call the researcher **once** and pass excerpts to the
  critic instead of having both re-read the whole file.
- **`[team]` is a thread tally, not a turn log.** If you want a per-turn view, the
  `[trace]` block boundaries (`agent: desk`) delimit turns; the *last* `agent: desk` and
  everything after it is the current turn.
- **The order is advisory.** Because orchestration is the lead model following its prompt,
  the only way to *force* an order is to hard-code it in Python (call the sub-agents
  yourself in sequence) rather than handing them to one lead as tools. research-desk
  deliberately uses the soft, prompt-driven approach — more flexible, less deterministic.
- **Sub-agents are context firewalls.** The researcher can burn tokens reading files, but
  only its short returned string enters the lead's context. That is the practical reason to
  use sub-agents even in this simple hierarchy: the lead's window stays small.

---

## 7. Source map

If you want to verify any claim here against the code:

| Claim | File |
|-------|------|
| Sub-agent = agent wrapped as a tool | [`aisuite/agents/tools.py`](../../aisuite/agents/tools.py) — `agent_tool` |
| The lead's tool loop (one model call per iteration) | [`aisuite/client.py`](../../aisuite/client.py) — `_tool_runner` |
| Steps = `[prior, agent, model_responses, tools]` | [`aisuite/agents/runner.py`](../../aisuite/agents/runner.py) — `run_sync` |
| `prior_steps` carried across turns | `runner.py` — the `RunState` branch |
| `[team]` / `[trace]` printers | [`desk.py`](desk.py) — `print_turn_trace` |
