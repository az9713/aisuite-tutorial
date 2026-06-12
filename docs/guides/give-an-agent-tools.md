# Give an agent tools

Attach capabilities to an agent — your own Python functions, prebuilt toolkits, or both — so it can act, not just answer.

**When you need this:** any agent that must read files, call an API, run a command, or otherwise do something beyond generating text.

## Prerequisites

- aisuite installed, with a working model string and key (see [prerequisites](../getting-started/prerequisites.md)).

## Option A: your own functions

Write a normal Python function with type annotations and a docstring. aisuite generates the schema from it.

```python
import aisuite as ai
from aisuite import Agent, Runner

def get_stock_price(ticker: str) -> str:
    """Return the latest closing price for a ticker.

    Args:
        ticker (str): The stock symbol, e.g. "AAPL".
    """
    return fetch_price(ticker)   # your implementation

agent = Agent(
    name="market-helper",
    model="openai:gpt-4o",
    instructions="Answer questions about stock prices using your tools.",
    tools=[get_stock_price],
)

result = Runner.run_sync(agent, "What's AAPL trading at?")
print(result.final_output)
```

Every parameter must be annotated (an unannotated one raises `TypeError`), and the docstring's `Args:` section becomes the parameter descriptions the model sees.

## Option B: prebuilt toolkits

Toolkits give you sandboxed file, git, and shell tools without writing them. Spread them into `tools` with `*`:

```python
agent = Agent(
    name="repo-helper",
    model="anthropic:claude-sonnet-4-6",
    instructions="Answer from the code in this repo.",
    tools=[
        *ai.toolkits.files(root="."),
        *ai.toolkits.git(root="."),
    ],
)
result = Runner.run_sync(agent, "What changed in the last commit?")
```

By default `files(root=".")` exposes read-only tools. To allow writes, pass `allow_write=True` — but note the write tools are marked `requires_approval=True`, so pair them with an approval policy (see [require approval for tools](require-approval-for-tools.md)).

## Option C: mix everything

Functions, toolkits, and MCP tools all go in the same list:

```python
agent = Agent(
    name="assistant",
    model="openai:gpt-4o",
    tools=[
        get_stock_price,                       # your function
        *ai.toolkits.files(root="./data"),     # a toolkit
    ],
)
```

For MCP servers, see [connect an MCP server](connect-an-mcp-server.md).

## Without the Agents API

If you don't need the full Agents API, the same tools work directly on a completion with `max_turns`:

```python
client = ai.Client()
response = client.chat.completions.create(
    model="openai:gpt-4o",
    messages=[{"role": "user", "content": "What's AAPL trading at?"}],
    tools=[get_stock_price],
    max_turns=3,
)
print(response.choices[0].message.content)
```

## Verification

Run the agent and inspect what it did:

```python
result = Runner.run_sync(agent, "What's AAPL trading at?")
for step in result.steps:
    print(step.type, step.name)   # look for tool_call / tool_result steps
```

If you see a `tool_call` step naming your function, the model used it. If it only produced text without calling the tool, sharpen the function's docstring and the agent's instructions.

## Troubleshooting

**`TypeError: ... missing a type annotation`** — annotate every parameter; aisuite needs the types to build the schema.

**The model never calls the tool** — the description is too vague. The docstring summary and `Args:` are the only signal the model has. Make them specific, and tell the agent in its `instructions` to use the tools.

**`One or more tools is not callable`** — you passed something that isn't a function (or an OpenAI-format spec) in `tools`. Toolkits must be spread with `*` since each factory returns a *list* of callables.

## Related

- [Tool calling concept](../concepts/tool-calling.md) — how schemas are generated and the loop runs.
- [Toolkits concept](../concepts/toolkits.md) — what each toolkit exposes.
- [Require approval for tools](require-approval-for-tools.md) — gating risky tools.
