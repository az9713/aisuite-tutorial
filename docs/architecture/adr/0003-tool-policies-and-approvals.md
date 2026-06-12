# ADR 0003: Tool governance as a separate policy primitive

**Status:** Accepted

## Context

Agents that can write files or run shell commands need governance — allowlists, denials, and human approval for risky actions. The question was where that governance lives.

Constraints:
- The same tool should be ungated in one context (a trusted batch job) and approval-gated in another (an interactive desktop app), without changing the tool.
- Approval can't always be a blocking prompt; UI-driven harnesses need to pause a run, surface the pending action, and resume after a human decides.
- Governance decisions must be auditable.

## Decision

Make governance a **separate primitive**: a `ToolPolicy` evaluated before every tool call, decoupled from tool definitions. A policy receives a `ToolPolicyContext` (tool name, arguments, the tool's declared `ToolMetadata`, conversation, run identity) and returns a `ToolPolicyDecision`. Tools declare *intent* (`risk_level`, `requires_approval`) via `@tool`/`ToolMetadata`; policies decide *enforcement* per run. Built-ins cover the common cases (`AllowAllToolPolicy`, `DenyAllToolPolicy`, `AllowToolsPolicy`, `RequireApprovalPolicy`). A run needing a human decision can end `requires_input` and resume via `continue_sync`.

## Alternatives considered

### Option A: Enforcement inside each tool
Each tool checks permissions itself.
- **Pros:** co-located with the action.
- **Cons:** every tool reimplements gating; the same tool can't vary by context; no uniform audit; toolkit tools couldn't be governed by the host app.

### Option B: A global allow/deny config
One static config of allowed tools.
- **Pros:** simple.
- **Cons:** static — can't reflect arguments or conversation; no human-in-the-loop; not per-run.

### Option C: A pluggable policy evaluated per call (chosen)
Decision separated from definition; metadata declares intent, policy enforces.

## Rationale

Separating "what a tool is" from "whether this call is allowed right now" is what lets one toolkit serve a trusted automation and an interactive app unchanged — the difference is the policy passed at run time. Because the policy sees the full context (including arguments and the conversation), decisions can be as nuanced as "allow `write_file` under `./build` but prompt elsewhere." The `requires_input`/resume status makes non-blocking, UI-driven approval a first-class flow rather than a hack. Every decision is emitted as a `tool.allowed`/`tool.denied` trace event, giving a built-in audit trail.

## Trade-offs

- Two concepts to understand (metadata vs. policy) instead of one; a newcomer can be surprised that marking a tool `requires_approval=True` does nothing until a policy enforces it.
- The policy is a single evaluation point per call; complex multi-stage approvals must be composed inside a custom policy/callback.
- Pause/resume requires the harness to persist and reload run state, which couples robust approvals to a state store.

## Consequences

- Toolkits ship risk metadata; the host decides enforcement. OpenCoworker and the CLI both layer a `RequireApprovalPolicy` over the same toolkits.
- Audit comes for free via tracing.
- See [tool policies](../../concepts/tool-policies.md) and [require approval for tools](../../guides/require-approval-for-tools.md).
