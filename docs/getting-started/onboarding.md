# Onboarding: zero to hero

This is the patient walkthrough. By the end you'll understand what aisuite is, how its layers relate, and why it's built the way it is — before you write a line of code. If you just want to run something now, jump to the [Chat Completions quickstart](../chat-completions-quickstart.md) and come back here later.

## Start with an analogy

If you've used the OpenAI Python SDK, aisuite will feel familiar on purpose. You still write:

```python
client.chat.completions.create(model=..., messages=..., temperature=...)
```

The difference is the `model` argument. In the OpenAI SDK, `model` is just a model name and the client is hard-wired to OpenAI. In aisuite, `model` is a `provider:model` string, and one client talks to every provider. `openai:gpt-4o` and `anthropic:claude-sonnet-4-6` go through the same line of code. Swapping providers is editing a string, not rewriting an integration.

If you've used an agent framework before, the Agents API will feel familiar too — but lighter. There's no graph to define and no DSL to learn. An agent is a dataclass; you run it with a `Runner`; tools are plain Python functions.

## The core abstractions

Four ideas carry most of the library.

**The Client routes calls.** `ai.Client()` is the front door. When you call `create(model="anthropic:claude-...")`, the client splits the string at the colon, finds the matching provider adapter, and hands off. The adapter translates your request into Anthropic's SDK call and translates the answer back into a uniform `ChatCompletionResponse`. You always read the result the same way: `response.choices[0].message.content`.

**Providers are discovered by convention.** There is no central registry to edit. A provider is a file named `<name>_provider.py` containing a class `<Name>Provider`. The `ProviderFactory` finds it by globbing the providers directory. Adding Groq support means adding `groq_provider.py` — nothing else. This is why the supported-provider list is "whatever files exist," and why contributing a provider is a small, self-contained change.

**Tools are just functions.** To give a model a tool, you pass a Python function. aisuite reads its signature and docstring, builds the JSON schema the model needs, and — when the model decides to call it — validates the arguments, runs your function, and feeds the result back. You never hand-write a schema. Set `max_turns` and aisuite runs the whole call-execute-respond loop for you; omit it and you drive the loop yourself.

**An Agent is a blueprint; a Runner executes it.** An `Agent` bundles a model, instructions, and tools into a reusable definition that holds no state. `Runner.run(agent, "your input")` executes it and returns a `RunResult`. Everything a production harness needs hangs off the Runner: policies decide which tool calls are allowed, state stores persist conversations so they can resume later, artifact stores keep huge payloads out of the message history, and tracing records every step.

## Why it works this way

Three design choices surprise people. Here's the reasoning.

**Why one string instead of separate clients per provider?** Because the thing you want to vary at runtime — and in experiments, and in fallbacks — is the model. Making the provider part of the model string means model selection is data, not code. You can read it from config, loop over a list, or A/B two providers without branching your code.

**Why generate schemas from functions instead of asking for JSON?** Because the function signature and docstring already contain everything the schema needs: parameter names, types, and descriptions. Writing the schema by hand duplicates that information and lets it drift out of sync. aisuite treats the function as the single source of truth. (You can still pass raw JSON specs when you want manual control — both styles are supported.)

**Why build policies, state, and tracing into the agent loop instead of leaving them to the app?** Because every serious agent harness reinvents them, usually late and badly. Approval gates, resumable threads, and step-level observability are not optional extras for real work — they're the difference between a demo and something you'd let touch your files. aisuite ships them as composable primitives so you don't rebuild them, and OpenCoworker proves they're sufficient for a real product.

## A realistic scenario, narrated

Picture building a "repo assistant" that answers questions about a codebase.

You declare an agent: a model string, a one-line instruction ("answer from the code"), and tools assembled from two toolkits — `files(root=".")` for reading and searching, and `git(root=".")` for status and diffs. Toolkits are sandboxed: every path the file tools touch is resolved against `.` and anything escaping that root is refused.

You run it: `Runner.run(agent, "What changed in the last commit? Summarize in three bullets.")`.

Behind the scenes, the Runner opens a trace context and calls the model with your tools' schemas attached. The model can't see your repo, so it asks to call `git_diff`. aisuite checks the active tool policy — `git_diff` is read-only and low-risk, so it's allowed — runs the function inside the repo root, and returns the diff text to the model. The model reads it and produces three bullets. The loop ends.

You get back a `RunResult`. `result.final_output` is the summary. `result.steps` is the ordered list of what happened: the agent step, the model response, the `git_diff` call, its result, the final response. `result.trace_id` lets you open this exact run in the trace viewer and watch the timeline.

Now suppose you want this assistant to also *fix* things. You enable writes: `files(root=".", allow_write=True)`. That exposes `write_file` and `apply_unified_diff` — but those are marked `risk_level="medium"` and `requires_approval=True`. You attach a `RequireApprovalPolicy` whose callback prompts you (or your UI) before any write runs. Now the agent can propose an edit, but a human approves it before it touches disk. That single switch — a policy — is exactly how OpenCoworker gates risky actions.

Finally, you want the conversation to survive a restart. You pass a `FileStateStore` and a `thread_id`. The Runner saves the thread's `RunState` after each run; later, `Runner.continue_sync(agent, "now also check the tests", state_store=store, thread_id="repo-chat")` reloads the thread and picks up where it left off.

That's the whole arc: route a call, give it tools, gate the risky ones, persist the thread, watch the trace. The same five moves scale from a notebook to OpenCoworker.

## Where to go next

A curated path:

1. **[Chat Completions quickstart](../chat-completions-quickstart.md)** — run your first multi-provider completion.
2. **[Agents quickstart](../agents-quickstart.md)** — tools, the Agents API, policies, and MCP in one pass.
3. **[Concepts: the Agents API](../concepts/agents-api.md)** — how `Runner` actually executes.
4. **[Concepts: tool policies](../concepts/tool-policies.md)** — approvals and allowlists in depth.
5. **[Guides](../guides/)** — task-shaped recipes when you have a specific goal.
6. **[OpenCoworker](../components/opencoworker.md)** — read the reference harness, or just [download the app](../opencoworker-quickstart.md).
