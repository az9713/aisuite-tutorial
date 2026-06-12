# Require approval for tools

Gate risky tool calls behind a human decision, so an agent can propose an action but a person approves it before it runs.

**When you need this:** any agent that can write files, run shell commands, send messages, or take other irreversible actions.

## Prerequisites

- An agent with tools (see [give an agent tools](give-an-agent-tools.md)).
- An understanding that the toolkits already mark writes and shell as `requires_approval=True` — but metadata alone enforces nothing; a policy does.

## Steps

### 1. Write an approval callback

The callback receives a `ToolPolicyContext` and returns `True` (allow), `False` (deny), or a `ToolPolicyDecision` (with a reason):

```python
from aisuite import RequireApprovalPolicy, ToolPolicyContext

def approve(ctx: ToolPolicyContext) -> bool:
    print(f"Agent {ctx.agent_name} wants: {ctx.tool_name}({ctx.arguments})")
    return input("Allow? [y/N] ").strip().lower() == "y"

policy = RequireApprovalPolicy(approve)
```

### 2. Only prompt for risky calls

Auto-approve low-risk tools and prompt only when the tool declares it needs approval:

```python
def approve(ctx: ToolPolicyContext) -> bool:
    md = ctx.tool_metadata
    if md and md.requires_approval:
        print(f"⚠ {ctx.tool_name}({ctx.arguments}) — risk={md.risk_level}")
        return input("Allow? [y/N] ").strip().lower() == "y"
    return True   # low-risk reads run without a prompt
```

### 3. Attach it to the run

```python
import aisuite as ai
from aisuite import Agent, Runner

agent = Agent(
    name="editor",
    model="anthropic:claude-sonnet-4-6",
    instructions="Make the requested code edits.",
    tools=[*ai.toolkits.files(root=".", allow_write=True)],
)

result = Runner.run_sync(agent, "Add a docstring to main() in app.py",
                         tool_policy=policy)
print(result.final_output)
```

Now `read_file` and `list_files` run freely, but `write_file` and `apply_unified_diff` prompt you first.

## Alternative: an allowlist instead of approval

If you don't want interactive prompts at all, deny risky tools outright with an allowlist:

```python
from aisuite import AllowToolsPolicy

policy = AllowToolsPolicy(["read_file", "list_files", "search_files",
                           "git_status", "git_diff"])
# the agent is now strictly read-only
```

## Alternative: pause-and-resume (for UIs)

In a non-interactive harness, don't block on `input()`. Instead let the run end with `status == "requires_input"`, surface the pending action to your UI, then resume:

```python
result = Runner.run_sync(agent, "Edit app.py", tool_policy=ui_policy,
                         state_store=store, thread_id="edit-1")
if result.status == "requires_input":
    decision = await ask_user_in_ui(result)        # your UI
    result = Runner.continue_sync(agent, decision,
                                  state_store=store, thread_id="edit-1")
```

This is how OpenCoworker renders approval cards.

## Verification

Check that denials and approvals are recorded:

```python
result = Runner.run_sync(agent, "Edit app.py", tool_policy=policy)
for step in result.steps:
    if step.type in ("tool_call", "tool_result"):
        print(step.name, step.data.get("allowed"), step.data.get("reason"))
```

Or open the run in the [trace viewer](view-traces.md): allowed and denied calls appear inline in the timeline.

## Troubleshooting

**`TypeError: Approval callback must return a bool or ToolPolicyDecision`** — your callback returned something else (a string, `None`). Return a `bool` or a `ToolPolicyDecision`.

**Writes still run without prompting** — you attached the policy at run time but the tool isn't flagged. The toolkit write tools are flagged automatically; for your own tools, decorate them with `@tool(metadata=ToolMetadata(requires_approval=True, risk_level="high"))`.

**The prompt blocks a server** — don't use `input()` in a web app. Use the pause-and-resume pattern above.

## Related

- [Tool policies concept](../concepts/tool-policies.md) — the full policy model.
- [Toolkits concept](../concepts/toolkits.md) — which tools are flagged.
- [Persist and resume runs](persist-and-resume-runs.md) — the resume mechanics.
