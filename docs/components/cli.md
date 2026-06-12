# aisuite-code CLI

A local coding-agent CLI built on aisuite: an approval-gated conversation loop scoped to a project directory, with file and shell tools and trace output for the viewer. Source: [`cli/py/`](https://github.com/andrewyng/aisuite/tree/main/cli/py).

## What it is

`aisuite-code` is a terminal coding assistant — a small reference application showing the Agents API, toolkits, and tool policies working together. It reads and (with approval) edits files in a working directory, runs a restricted set of shell commands, and writes traces you can open in the aisuite viewer.

## Install and run

It's a Poetry project under `cli/py/aisuite-code-cli/`:

```bash
cd cli/py/aisuite-code-cli
python3 -m poetry install
python3 -m poetry run aisuite-code --cwd /path/to/project
```

Or from the repo root via the helper script:

```bash
./scripts/aisuite-code --cwd /path/to/project
```

Default model is `openai:gpt-4o-mini`, so set `OPENAI_API_KEY` (or pass `--model` for another provider).

## Flags

| Flag | Default | Effect |
|------|---------|--------|
| `--cwd` | `.` | Working directory the agent is scoped to. |
| `--model` | `openai:gpt-4o-mini` | A `provider:model` string. |
| `--mode` | — | Permission mode: `plan`, `interactive`, or `auto`. |
| `--resume SESSION_ID` | — | Resume a previous session. |
| `--viewer` | off | Start the trace viewer automatically. |
| `--allow-shell-all` | off | Permit any shell command (otherwise restricted to a safe set). |
| `--no-reviewer` | off | Disable the read-only reviewer subagent. |

## In-session commands

| Command | Does |
|---------|------|
| `/help` | Show help. |
| `/viewer` / `/viewer start` | Manage / start the trace viewer. |
| `/status` | Show model, cwd, trace file, artifact root, shell policy. |
| `/clear` | Clear the conversation. |
| `/exit` | Quit. |

## How it works

- **Read-only by default.** File reads and searches run freely; writes and shell commands require approval (a `RequireApprovalPolicy` over the [files](../concepts/toolkits.md) and [shell](../concepts/toolkits.md) toolkits).
- **Restricted shell.** Only a safe command set (git, npm, python, …) is allowed unless `--allow-shell-all`.
- **Reviewer subagent.** A read-only `review_changes(input)` subagent is available to the main agent (disable with `--no-reviewer`) — an example of [subagents via `agent_tool`](../concepts/agents-api.md#subagents).
- **Traces.** Runs are written as JSONL and viewable in the [aisuite viewer](../guides/view-traces.md). Use `--viewer` or `/viewer start`.

See `cli/py/aisuite-code-cli/TRY_IT.md` for a hands-on walkthrough.

## Relationship to OpenCoworker

The CLI is a lightweight, terminal-only sibling of [OpenCoworker](opencoworker.md). Both build on the same aisuite primitives — agents, toolkits, policies, tracing — but the CLI stays in one project directory with a coding focus, while OpenCoworker is a full desktop app with a GUI, connectors, and automations.

## Related

- [The Agents API](../concepts/agents-api.md)
- [Toolkits](../concepts/toolkits.md) and [tool policies](../concepts/tool-policies.md)
- [Guide: view traces](../guides/view-traces.md)
