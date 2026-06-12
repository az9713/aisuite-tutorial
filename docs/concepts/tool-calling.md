# Tool calling

aisuite turns tool calling into a one-liner: pass plain Python functions and it generates the schemas, executes the calls, and feeds results back to the model.

## What it is

Two styles share one entry point, `client.chat.completions.create(..., tools=[...])`:

- **Automatic** — set `max_turns` and aisuite runs the whole loop (send → execute tools → return results → repeat) until the model stops requesting tools or the turn cap is hit.
- **Manual** — omit `max_turns` and aisuite returns the model's tool-call requests for you to execute, validate, or filter yourself.

## From a function to a schema

When you pass a callable, the `Tools` class (`aisuite/utils/tools.py`) builds an OpenAI-format tool spec from it:

```python
def will_it_rain(location: str, time_of_day: str):
    """Check if it will rain in a location at a given time today.

    Args:
        location (str): Name of the city
        time_of_day (str): Time of the day in HH:MM format.
    """
    return "YES"
```

aisuite reads:

- **The name** from `func.__name__`.
- **The description** from the docstring summary.
- **Parameters and types** from the signature annotations (every parameter must be annotated — an unannotated parameter raises `TypeError`).
- **Parameter descriptions** from the docstring's `Args:` section, parsed with `docstring_parser`.

It produces:

```json
{
  "type": "function",
  "function": {
    "name": "will_it_rain",
    "description": "Check if it will rain in a location at a given time today.",
    "parameters": {
      "type": "object",
      "properties": {
        "location": {"type": "string", "description": "Name of the city"},
        "time_of_day": {"type": "string", "description": "Time of the day in HH:MM format."}
      },
      "required": ["location", "time_of_day"]
    }
  }
}
```

The function is the single source of truth — there is no separate schema to keep in sync.

## Automatic execution with `max_turns`

```python
client = ai.Client()
response = client.chat.completions.create(
    model="openai:gpt-4o",
    messages=[{"role": "user",
               "content": "I'm in San Francisco. Check the weather and plan a 2pm picnic."}],
    tools=[will_it_rain],
    max_turns=2,
)
print(response.choices[0].message.content)
```

The loop (`Completions._tool_runner`):

1. Send `messages` and the tool schemas to the provider.
2. If the response has no `tool_calls`, return it.
3. Otherwise, execute each requested tool, append the assistant message and `tool` result messages, and loop — up to `max_turns` times.

After it returns:

- `response.choices[0].message.content` — the final answer.
- `response.choices[0].intermediate_messages` — the full tool-interaction history (assistant tool-call messages plus `tool` results). Append it to your `messages` to continue the conversation.
- `response.intermediate_responses` — the raw responses from each intermediate turn.

## Argument validation and execution

Before your function runs, aisuite validates the model's arguments against a Pydantic model derived from the signature. The model returns arguments as a JSON string; aisuite parses it, validates it, and calls your function with typed keyword arguments. A validation failure surfaces rather than passing bad data into your code.

`execute_tool(...)` also returns the `tool`-role messages the model needs to read the results, and — when tool policies are in play — applies them and records `tool.*` trace events.

## Manual tool handling

Omit `max_turns` to drive the loop yourself. Pass OpenAI-format JSON specs (or callables) and aisuite returns the model's requested calls without executing them:

```python
tools = [{
    "type": "function",
    "function": {
        "name": "will_it_rain",
        "description": "Check if it will rain in a location at a given time today",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "Name of the city"},
                "time_of_day": {"type": "string", "description": "Time of the day in HH:MM format."}
            },
            "required": ["location", "time_of_day"]
        }
    }
}]

response = client.chat.completions.create(
    model="openai:gpt-4o", messages=messages, tools=tools,
)
# response.choices[0].message.tool_calls holds the requested calls — you run them.
```

This suits custom error handling, selective execution, or integrating an existing tool pipeline. Both styles are demonstrated in `examples/tool_calling_abstraction.ipynb`.

## Tools that carry metadata

Attach `ToolMetadata` to a function with the `@tool` decorator to give policies something to reason about (risk level, category, approval requirement):

```python
from aisuite import tool, ToolMetadata

@tool(metadata=ToolMetadata(category="filesystem", risk_level="high", requires_approval=True))
def delete_everything(path: str):
    """Delete a directory tree."""
    ...
```

The toolkits use exactly this mechanism to mark writes and shell commands. See [tool policies](tool-policies.md).

## MCP tools

You can also mix Model Context Protocol tools into the same `tools=[...]` list, either as inline config dicts or via an explicit `MCPClient`. See [MCP](mcp.md).

## Related

- [The Agents API](agents-api.md) — the higher-level way to run tool loops.
- [Tool policies](tool-policies.md) — gating which calls run.
- [reference/client-api.md](../reference/client-api.md) — `create` parameters in full.
