# Tool policies

A tool policy decides whether a given tool call is allowed to run. Policies are how you turn a capable agent into a *safe* one — adding allowlists, denials, and human approval gates without changing the tools themselves.

## What it is

A policy is an object with an `evaluate(context) -> ToolPolicyDecision` method (or a plain callable). Before any tool executes, aisuite calls the active policy with a `ToolPolicyContext` describing the pending call. The policy returns a `ToolPolicyDecision`; if it's not allowed, the call is skipped and recorded as denied.

You attach a policy at run time:

```python
result = Runner.run_sync(agent, "Refactor utils.py", tool_policy=my_policy)
```

It also works at the Chat Completions layer via `tool_policy=` on `create(...)`.

## The decision types

```python
@dataclass
class ToolPolicyDecision:
    allowed: bool
    reason: Optional[str] = None
    metadata: dict = {}
```

```python
@dataclass
class ToolPolicyContext:
    agent_name: str
    tool_name: str
    arguments: dict
    run_name: Optional[str]
    trace_id: Optional[str]
    group_id: Optional[str]
    tags: list[str]
    metadata: dict
    messages: list[dict]              # conversation so far
    parent_run_id: Optional[str] = None
    tool_metadata: Optional[ToolMetadata] = None   # risk_level, requires_approval, ...
```

A policy can decide on anything it sees — the tool's name, its arguments, its declared `risk_level`, or the conversation context.

## Built-in policies

| Policy | Behavior |
|--------|----------|
| `AllowAllToolPolicy()` | Every call allowed. The implicit default. |
| `DenyAllToolPolicy(reason=None)` | Every call denied. Useful for dry-runs. |
| `AllowToolsPolicy(allowed_tools, reason=None)` | Allow only tools whose name is in the allowlist; deny the rest. |
| `RequireApprovalPolicy(callback)` | Defer to your callback for each call. |

```python
from aisuite import AllowToolsPolicy

policy = AllowToolsPolicy(["read_file", "list_files", "git_status", "git_diff"])
# read-only agent: writes and shell are denied
```

## Approval flows

`RequireApprovalPolicy` calls a function you supply for every tool call. Return a `bool` (or a `ToolPolicyDecision` for a reason):

```python
from aisuite import RequireApprovalPolicy, ToolPolicyContext

def approve(ctx: ToolPolicyContext) -> bool:
    print(f"{ctx.agent_name} wants to call {ctx.tool_name}({ctx.arguments})")
    return input("Allow? [y/N] ").strip().lower() == "y"

policy = RequireApprovalPolicy(approve)
result = Runner.run_sync(agent, "Clean up the temp files", tool_policy=policy)
```

The callback must return a `bool` or `ToolPolicyDecision`; anything else raises `TypeError`.

A common pattern combines metadata and approval: mark risky tools `requires_approval=True` (the toolkits already do this for writes and shell), then write a callback that auto-approves low-risk calls and prompts only when `ctx.tool_metadata.requires_approval` is set:

```python
def approve(ctx):
    if ctx.tool_metadata and ctx.tool_metadata.requires_approval:
        return ask_human(ctx)        # your UI / prompt
    return True                       # low-risk: allow silently
```

## Pausing and resuming for human input

For non-interactive or UI-driven harnesses, an approval often isn't a blocking prompt — the run pauses and waits. A run that needs a human decision ends with `status == "requires_input"`. The harness surfaces the pending action, collects the human's answer, and resumes with `Runner.continue_sync(...)`. This is exactly how OpenCoworker renders approval cards: the agent proposes, the run pauses, the user clicks Allow or Deny, and the run continues. See [the Agents API](agents-api.md#continuing-a-conversation) for the resume mechanics.

## Tracing denials and approvals

Every policy decision is emitted as a trace event — `tool.allowed` or `tool.denied`, followed by `tool.started`/`tool.completed`/`tool.failed` for calls that run. The [trace viewer](tracing.md) shows approvals and denials inline in the timeline, so you can audit exactly what an agent was and wasn't permitted to do.

## Attaching metadata to your own tools

Use the `@tool` decorator to declare a custom tool's risk profile so policies can reason about it:

```python
from aisuite import tool, ToolMetadata

@tool(metadata=ToolMetadata(
    category="billing", risk_level="high", requires_approval=True,
    description="Issue a refund."))
def issue_refund(order_id: str, amount_cents: int):
    """Refund an order."""
    ...
```

## Related

- [Toolkits](toolkits.md) — the risk levels the built-in tools declare.
- [The Agents API](agents-api.md) — where policies plug in and how runs resume.
- [Guide: require approval for tools](../guides/require-approval-for-tools.md).
- [ADR 0003](../architecture/adr/0003-tool-policies-and-approvals.md) — why policies are a separate primitive.
