# What is aisuite?

aisuite is a Python library that gives you one consistent way to call any LLM provider, plus an Agents API for turning those models into tool-using agents.

## The problem it solves

Every LLM provider has its own SDK, its own request and response shapes, and its own way of declaring tools. Writing code against OpenAI and then moving to Anthropic, Google, or a local Ollama model normally means rewriting the integration. aisuite removes that cost: you write your logic once against an OpenAI-style interface and switch models by changing one string.

On top of that, building a tool-using agent usually means hand-writing JSON schemas for every function, running the call-execute-respond loop yourself, and inventing your own approval, persistence, and observability layers. aisuite ships those as first-class pieces.

## The mental model

Think of aisuite as three stacked layers, each usable on its own:

1. **Chat Completions API** — a unified, OpenAI-shaped interface over 20+ providers. Model names are `provider:model` strings (for example `openai:gpt-4o` or `anthropic:claude-sonnet-4-6`), and aisuite routes each call to the right provider adapter, translating parameters and responses both ways.

2. **Agents API, Toolkits, and MCP** — give a model real Python functions as tools, run multi-turn tool loops, attach prebuilt sandboxed toolkits (files, git, shell) or any Model Context Protocol server, and govern execution with tool policies. Runs can be persisted, resumed, and traced.

3. **OpenCoworker** — a desktop application built on the layers below it. It is both a product you can download and a working reference for building your own agent harness on aisuite.

The key design choice: **each layer is independently useful**. You can ship a product on just the Chat Completions API. You can adopt the Agents API without ever installing the desktop app. Nothing forces you up the stack.

## Architecture overview

```text
        your code
            │
            ▼
   ┌─────────────────┐
   │     Client      │   ai.Client() — the entry point
   │  chat.completions.create(model="provider:model", ...)
   └────────┬────────┘
            │  splits "provider:model", looks up the adapter
            ▼
   ┌─────────────────┐
   │ ProviderFactory │   discovers providers/<name>_provider.py by convention
   └────────┬────────┘
            │
   ┌────────▼────────────────────────────────────────────┐
   │  Provider adapters (OpenAI, Anthropic, Google, ...)  │
   │  each implements chat_completions_create(...)        │
   └────────┬────────────────────────────────────────────┘
            │  returns a normalized ChatCompletionResponse
            ▼
   response.choices[0].message.content


   Agents layer (built on Client):

   Agent ──run──▶ Runner ──▶ Client.chat.completions.create(max_turns=...)
     │                          │
     │                          ├─ Tools: Python fns → JSON schemas → execute
     │                          ├─ Tool policies: allow / deny / approve
     │                          ├─ State stores: persist & resume threads
     │                          ├─ Artifact stores: offload large payloads
     │                          └─ Tracing: emit events to sinks → viewer
     ▼
   RunResult (final_output, steps, trace_id, ...)
```

## How it all fits together — a typical flow

A developer wants an agent that answers questions about a git repo:

1. They declare an `Agent` with a model string, instructions, and tools assembled from `ai.toolkits.files(root=".")` and `ai.toolkits.git(root=".")`.
2. They call `Runner.run(agent, "What changed in the last commit?")`.
3. The Runner sets up a trace context and calls `client.chat.completions.create(...)` with `max_turns` and the tool schemas auto-generated from the toolkit functions.
4. The model asks to call `git_diff`; aisuite checks the active tool policy, runs the function inside its sandboxed root, feeds the result back, and loops until the model produces a final answer.
5. Every model call, tool call, and approval is emitted as a trace event, viewable later in the trace viewer.
6. The call returns a `RunResult` with `final_output`, the full step list, and a `trace_id`.

The same primitives — provider routing, tool loops, policies, state, tracing — are exactly what OpenCoworker uses under the hood.

## What aisuite is not

- **Not a hosted service.** There is no aisuite backend. Model calls go directly from your process (or OpenCoworker on your machine) to the provider you configured. Your keys and data stay local.
- **Not a prompt framework.** aisuite does not impose chains, graphs, or a DSL. You write plain Python; it handles provider plumbing and the agent loop.
- **Not a model.** aisuite calls models; it does not host or fine-tune them.
- **Not a full re-implementation in every language.** The Python library is the complete product. [aisuite-js](../components/aisuite-js.md) is a TypeScript port of the Chat Completions layer only — no Agents API, toolkits, or MCP.

## Where to go next

- Build the mental model term by term in [Key concepts](key-concepts.md).
- Get hands-on with the [Chat Completions quickstart](../chat-completions-quickstart.md).
- For newcomers who want the full picture before touching code, read the [onboarding guide](../getting-started/onboarding.md).
