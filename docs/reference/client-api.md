# Reference: Client API

The `aisuite.Client` and its chat/audio interfaces. Import as `import aisuite as ai`.

## Client

```python
ai.Client(provider_configs: dict = {}, extra_param_mode: str = "warn")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `provider_configs` | dict | `{}` | Per-provider config, keyed by provider key. Each value is a dict of constructor options for that provider's adapter. |
| `extra_param_mode` | `"strict"` \| `"warn"` \| `"permissive"` | `"warn"` | How unknown audio-transcription parameters are handled. |

`provider_configs` example:

```python
ai.Client({
    "openai": {"api_key": "sk-..."},
    "aws": {"aws_access_key": "...", "aws_secret_key": "...", "aws_region": "us-west-2"},
})
```

Providers initialize lazily on first use; keys absent from `provider_configs` fall back to environment variables.

### Methods and properties

| Member | Description |
|--------|-------------|
| `client.configure(provider_configs: dict)` | Merge in more provider config; providers re-initialize lazily. |
| `client.chat` | The chat interface (`.completions.create(...)`). |
| `client.audio` | The audio interface (`.transcriptions.create(...)`). |

## chat.completions.create

```python
client.chat.completions.create(model: str, messages: list, **kwargs)
```

Routes to the provider named in `model` and returns a [`ChatCompletionResponse`](#chatcompletionresponse).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | str | yes | A `provider:model` string. No colon → `ValueError`. |
| `messages` | list[dict] | yes | OpenAI-shaped messages (`role` + `content`). |
| `temperature`, `max_tokens`, … | — | no | Core parameters, mapped per provider. |
| `tools` | list | no | Callables, OpenAI-format specs, or MCP config dicts. See [tool calling](../concepts/tool-calling.md). |
| `max_turns` | int | no | If set with `tools`, runs the automatic tool loop up to this many turns. |
| `tool_policy` | ToolPolicy | no | Gate tool calls. See [policies](policies-and-stores.md). |
| `tool_policy_context` | dict | no | Extra context passed into policy evaluation. |
| `**kwargs` | — | no | Passed through to the provider SDK. |

### Errors

| Error | Cause |
|-------|-------|
| `ValueError: Invalid model format` | `model` has no colon. |
| `ValueError: Invalid provider key` | Provider not found by `ProviderFactory`. |
| `ImportError: MCP tools require the 'mcp' package` | An MCP config dict was passed without `aisuite[mcp]` installed. |
| `ValueError: One or more tools is not callable` | A non-callable, non-spec item in `tools` during the tool loop. |

## ChatCompletionResponse

| Field | Type | Description |
|-------|------|-------------|
| `choices` | list[Choice] | Completion choices (usually one). |
| `usage` | CompletionUsage \| None | Token accounting. |

After an automatic tool loop, the response also carries `intermediate_responses`, `tool_policy_events`, and `tool_events`.

### Choice

| Field | Type | Description |
|-------|------|-------------|
| `finish_reason` | `"stop"` \| `"tool_calls"` \| None | Why generation stopped. |
| `message` | Message | The assistant's reply. |
| `intermediate_messages` | list[Message] | Tool-interaction history (populated by the `max_turns` loop). |

### Message

| Field | Type | Description |
|-------|------|-------------|
| `role` | `"user"` \| `"assistant"` \| `"system"` \| `"tool"` \| None | Message role. |
| `content` | str \| None | Text content. |
| `reasoning_content` | str \| None | Extended-thinking text (extracted from `<think>` blocks). |
| `tool_calls` | list[ChatCompletionMessageToolCall] \| None | Requested tool calls. |
| `refusal` | str \| None | Refusal explanation, if the model refused. |

`ChatCompletionMessageToolCall`: `id: str`, `type: "function"`, `function: Function`. `Function`: `name: str`, `arguments: str` (a JSON string).

### CompletionUsage

| Field | Type | Description |
|-------|------|-------------|
| `prompt_tokens` | int \| None | Input tokens. |
| `completion_tokens` | int \| None | Output tokens. |
| `total_tokens` | int \| None | Sum. |
| `prompt_tokens_details` | object \| None | Breakdown: `text_tokens`, `audio_tokens`, `cached_tokens`. |
| `completion_tokens_details` | object \| None | Breakdown: `reasoning_tokens`, `audio_tokens`, `accepted_prediction_tokens`, `rejected_prediction_tokens`. |

## Audio transcription

```python
client.audio.transcriptions.create(*, model: str, file, **kwargs)
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | str | yes | `provider:model`, e.g. `openai:whisper-1`, `deepgram:nova-2`. |
| `file` | str \| BinaryIO | yes | Audio file path or file-like object. |
| `language` | str | no | Common, portable (e.g. `"en"`). |
| `prompt` | str | no | Common, portable context. |
| `temperature` | float | no | Common (OpenAI). |
| `stream` | bool | no | Request streaming output (provider-dependent). |
| `**kwargs` | — | no | Provider-specific (e.g. Deepgram `diarize`, `punctuate`). |

Common parameters are auto-mapped to each provider; unknown parameters follow `extra_param_mode`. Returns a `TranscriptionResponse` (batch or streaming). Providers without audio support raise `ValueError`.

`extra_param_mode` behavior:

| Mode | On unknown param |
|------|------------------|
| `strict` | raise `ValueError` |
| `warn` (default) | log a warning, pass through |
| `permissive` | pass through silently |

## Tools (manual schema generation)

`ai.Tools` exposes the schema-generation machinery directly:

```python
from aisuite import Tools
t = Tools([my_function])
t.tools()                      # OpenAI-format specs for the functions
results, messages = t.execute_tool(tool_calls)   # validate + run + format results
```

See [tool calling](../concepts/tool-calling.md).

## Related

- [Chat Completions concept](../concepts/chat-completions.md)
- [reference/agents-api.md](agents-api.md)
- [reference/providers.md](providers.md)
