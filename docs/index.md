# aisuite documentation

`aisuite` is a lightweight Python library for building with LLMs, layered as a unified Chat Completions API across providers and an Agents API with tools and toolkits on top. This repo is also home to OpenCoworker, a desktop AI coworker built on aisuite.

New here? Start with [What is aisuite?](overview/what-is-this.md), then run the [Chat Completions quickstart](chat-completions-quickstart.md).

---

## Documentation

| Section | What's inside |
|---------|--------------|
| [Overview](overview/what-is-this.md) | The mental model, the layered architecture, and a glossary |
| [Getting started](getting-started/prerequisites.md) | Prerequisites, onboarding, and the three quickstarts |
| [Concepts](concepts/) | Deep dives: chat completions, providers, tool calling, the Agents API, toolkits, policies, state, MCP, tracing |
| [Guides](guides/) | Task-oriented how-tos: add a provider, give an agent tools, require approval, persist runs, connect MCP, view traces |
| [Reference](reference/) | Complete API, configuration, provider, and environment reference |
| [Components](components/) | The other deliverables: aisuite-js, the CLI, OpenCoworker, the trace viewer |
| [Architecture](architecture/system-design.md) | System design and Architecture Decision Records |
| [Troubleshooting](troubleshooting/common-issues.md) | The errors you'll actually hit, and their fixes |

## Quickstarts

| Quickstart | Gets you to |
|------------|-------------|
| [Chat Completions](chat-completions-quickstart.md) | First multi-provider completion in ~5 minutes |
| [Agents](agents-quickstart.md) | An agent with tools, policies, and MCP |
| [OpenCoworker](opencoworker-quickstart.md) | The desktop app doing real tasks on your files |

## The two-layer model

```text
┌───────────────────────────────────────────────┐
│                 OpenCoworker                  │   agent harness for everyday tasks
├───────────────────────────────────────────────┤
│        Agents API  ·  Toolkits  ·  MCP        │   build agents across multiple LLMs
├───────────────────────────────────────────────┤
│             Chat Completions API              │   one API across multiple LLM providers
├────────┬───────────┬────────┬────────┬────────┤
│ OpenAI │ Anthropic │ Google │ Ollama │ Others │
└────────┴───────────┴────────┴────────┴────────┘
```

You can use any layer on its own. The Chat Completions API works without ever touching agents; the Agents API builds on it; OpenCoworker is a full application built on both.
