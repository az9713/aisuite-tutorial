# Add a provider

Add support for a new LLM provider by writing one adapter file. aisuite discovers it by naming convention — there's no registry to edit.

**When you need this:** a provider aisuite doesn't ship, or an internal/self-hosted endpoint.

## Prerequisites

- A local checkout of aisuite (`pip install -e .` or a Poetry dev environment).
- The provider's API details: how to authenticate, the request shape, and the response shape. If it's OpenAI-compatible, this is trivial.

## Steps

### 1. Create the adapter file

Name it `aisuite/providers/<name>_provider.py`. The `<name>` is the provider key users will type in `provider:model` strings.

```python
# aisuite/providers/acme_provider.py
from aisuite.provider import Provider
from aisuite.framework.chat_completion_response import ChatCompletionResponse


class AcmeProvider(Provider):
    def __init__(self, **config):
        super().__init__()
        # Read credentials from config or environment.
        self.api_key = config.get("api_key") or os.environ.get("ACME_API_KEY")
        # ... set up an SDK client or httpx session ...

    def chat_completions_create(self, model, messages, **kwargs):
        # 1. Translate `messages` + kwargs into the provider's request.
        # 2. Call the provider.
        # 3. Normalize the result into a ChatCompletionResponse.
        response = ChatCompletionResponse()
        response.choices[0].message.content = ...      # the text
        response.choices[0].finish_reason = "stop"
        return response
```

The class name must be the capitalized key plus `Provider`: key `acme` → class `AcmeProvider`. This pairing is how `ProviderFactory` finds it.

### 2. Normalize the response

Callers always read `response.choices[0].message.content`, so map the provider's output onto the framework types:

- `response.choices[0].message.content` — the assistant text.
- `response.choices[0].message.tool_calls` — tool calls, if the provider returned any (as `ChatCompletionMessageToolCall` objects).
- `response.choices[0].finish_reason` — `"stop"` or `"tool_calls"`.
- `response.usage` — a `CompletionUsage` with `prompt_tokens` / `completion_tokens` / `total_tokens` when available.

> **Tip:** If your provider is OpenAI-compatible, subclass `OpenaiProvider` and just set the base URL — see `ollama_provider.py`, `deepseek_provider.py`, and `openrouter_provider.py` for one-screen examples.

### 3. Declare the dependency (if it needs an SDK)

If your adapter imports a vendor SDK, add it as an optional dependency and an extra in `pyproject.toml`:

```toml
[tool.poetry.dependencies]
acme-sdk = { version = "^1.0.0", optional = true }

[tool.poetry.extras]
acme = ["acme-sdk"]
```

Add it to the `all` extra too. Pure-`httpx` adapters need no extra.

### 4. Use it

```python
import aisuite as ai
client = ai.Client()
response = client.chat.completions.create(
    model="acme:acme-large-1",
    messages=[{"role": "user", "content": "Hello"}],
)
print(response.choices[0].message.content)
```

## Verification

Confirm discovery and a round-trip:

```python
from aisuite.provider import ProviderFactory
assert "acme" in ProviderFactory.get_supported_providers()
```

Then run a real completion (above) and check you get text back. Add a test under `tests/providers/` mirroring the existing provider tests.

## Troubleshooting

**`Invalid provider key 'acme'`** — the file isn't discovered. Check it's at `aisuite/providers/acme_provider.py` and the class is exactly `AcmeProvider`. Note `get_supported_providers()` is cached with `functools.cache`, so restart your Python process after adding the file.

**`ImportError` when the provider initializes** — the vendor SDK isn't installed. Add the extra and `pip install 'aisuite[acme]'`, or install the SDK directly.

**Responses look wrong / empty** — your normalization isn't mapping fields onto `ChatCompletionResponse`. Print the raw vendor response and confirm you're setting `choices[0].message.content`.

## Related

- [Providers concept](../concepts/providers.md) — the discovery mechanism.
- [reference/providers.md](../reference/providers.md) — the existing provider table.
