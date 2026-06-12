# The Chat Completions API

The Chat Completions API is aisuite's foundation: one OpenAI-shaped interface that routes to any provider. Everything else — tool calling, agents, OpenCoworker — is built on it.

## What it is

A single method, `client.chat.completions.create(model, messages, **kwargs)`, that accepts a `provider:model` string and produces a normalized response regardless of which vendor served the request.

## How a call flows

1. **Parse the model string.** `create` splits `model` at the first colon into `provider_key` and `model_name`. No colon → `ValueError("Invalid model format. Expected 'provider:model'")`.
2. **Validate the provider.** The `provider_key` is checked against `ProviderFactory.get_supported_providers()`. Unknown provider → `ValueError` listing the supported set.
3. **Lazily initialize the provider.** On first use, the client constructs the provider adapter via `ProviderFactory.create_provider(provider_key, config)` and caches it. The config comes from what you passed to `Client(...)` for that provider, or `{}`.
4. **Process tools (if any).** MCP config dicts in `tools` are converted to callable tools; see [the tool-calling concept](tool-calling.md) and [MCP](mcp.md).
5. **Dispatch.** The adapter's `chat_completions_create(model_name, messages, **kwargs)` runs, calling the vendor SDK and normalizing the result.
6. **Post-process.** aisuite extracts any `<think>...</think>` block into `message.reasoning_content` and returns a `ChatCompletionResponse`.

The relevant code is `Completions.create` in `aisuite/client.py`.

## Creating a client

```python
import aisuite as ai

client = ai.Client()                                   # keys from environment
client = ai.Client({"openai": {"api_key": "sk-..."}})  # keys in code
```

Per-provider config is a dict keyed by provider. AWS, for example, takes credentials and a region:

```python
client = ai.Client({
    "aws": {
        "aws_access_key": "...",
        "aws_secret_key": "...",
        "aws_region": "us-west-2",
    }
})
```

You can also call `client.configure({...})` later; providers initialize lazily on next use.

## The unified request

Core parameters are provider-agnostic — aisuite maps them to each SDK's conventions:

```python
response = client.chat.completions.create(
    model="anthropic:claude-sonnet-4-6",
    messages=[
        {"role": "system", "content": "Respond in Pirate English."},
        {"role": "user", "content": "Tell me a joke."},
    ],
    temperature=0.75,
    max_tokens=512,
)
```

`messages` follows the OpenAI shape: a list of `{"role": ..., "content": ...}` dicts with roles `system`, `user`, `assistant`, and `tool`. Provider-specific parameters you pass through `**kwargs` reach the underlying SDK; portability is your responsibility for those.

## The unified response

Every provider returns a `ChatCompletionResponse`:

```python
response.choices[0].message.content        # the assistant's text
response.choices[0].message.role           # "assistant"
response.choices[0].message.tool_calls     # tool calls, if any
response.choices[0].message.reasoning_content  # extended-thinking text, if any
response.choices[0].finish_reason          # "stop" or "tool_calls"
response.usage.prompt_tokens               # token accounting
response.usage.completion_tokens
response.usage.total_tokens
```

The shape mirrors OpenAI's, so code written against the OpenAI SDK reads aisuite responses with minimal change. Full field list in [reference/client-api.md](../reference/client-api.md).

## Swapping providers

Because the provider lives in the model string, switching is a one-line change — or a loop:

```python
for model in ["openai:gpt-4o", "anthropic:claude-3-5-sonnet-20240620", "ollama:llama3.3"]:
    response = client.chat.completions.create(model=model, messages=messages)
    print(model, "→", response.choices[0].message.content)
```

## Local models

Ollama and LM Studio expose OpenAI-compatible servers, so they're first-class providers with no API key:

```python
response = client.chat.completions.create(
    model="ollama:llama3.3",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

## Reasoning content

Some models emit chain-of-thought wrapped in `<think>...</think>`. aisuite strips that block from `content` and stores it on `message.reasoning_content`, so your displayed answer is clean while the reasoning stays available.

## Audio transcription

The client also exposes `client.audio.transcriptions.create(model="openai:whisper-1", file=...)`. Common parameters (`language`, `prompt`, `temperature`) are portable; provider-specific ones (Deepgram's `diarize`, `punctuate`) pass through. Unknown parameters are handled per the client's `extra_param_mode` (`strict` / `warn` / `permissive`). See [reference/client-api.md](../reference/client-api.md#audio-transcription).

## Related

- [Providers](providers.md) — how routing and adapters work.
- [Tool calling](tool-calling.md) — adding tools to a completion.
- [reference/client-api.md](../reference/client-api.md) — every parameter and field.
