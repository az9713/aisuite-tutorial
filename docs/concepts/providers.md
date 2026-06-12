# Providers

A provider is an adapter that translates aisuite's unified request into one vendor's SDK call and normalizes the response back. Providers are discovered by naming convention, so adding one is a self-contained change.

## The discovery convention

The `ProviderFactory` (in `aisuite/provider.py`) maps a provider key to code by convention — there is no registry list to edit:

| Element | Rule | Example (`openai`) |
|---------|------|-------------------|
| Module file | `<provider>_provider.py` | `openai_provider.py` |
| Class name | `<Provider>Provider` (capitalized key) | `OpenaiProvider` |
| Import path | `aisuite.providers.<provider>_provider` | — |

`create_provider(provider_key, config)` imports the module with `importlib.import_module` and instantiates the class with `**config`. `get_supported_providers()` globs `providers/*_provider.py` and returns the set of stems with `_provider` stripped — so "supported" literally means "a correctly named file exists." The result is cached with `functools.cache`.

> **Note:** Keys map directly to module names. AWS Bedrock is the `aws` provider key (`aws_provider.py` → `AwsProvider`), not `aws-bedrock`.

## The provider interface

Every provider subclasses the `Provider` abstract base class:

```python
class Provider(ABC):
    def __init__(self):
        self.audio: Optional[Audio] = None

    @abstractmethod
    def chat_completions_create(self, model, messages):
        ...
```

A provider must implement `chat_completions_create(self, model, messages, **kwargs)` and return a normalized `ChatCompletionResponse`. Optionally it sets `self.audio` to an object exposing `.transcriptions` to support audio transcription.

## How adapters normalize

Providers fall into three implementation styles:

- **Native SDK adapters** wrap a vendor SDK and map fields both ways — for example `AnthropicProvider` (the `anthropic` SDK), `GoogleProvider` (Vertex AI / `google.generativeai`), `MistralProvider`, `CohereProvider`, `WatsonxProvider`, `AwsProvider` (boto3 Bedrock Converse).
- **OpenAI-compatible adapters** point the `openai` SDK at a different base URL. `DeepseekProvider`, `OpenrouterProvider`, `NebiusProvider`, `SambanovaProvider`, `InceptionProvider`, `GroqProvider`, and the local `OllamaProvider` / `LmstudioProvider` all work this way (the last two inherit from `OpenaiProvider`).
- **Raw HTTP adapters** use `httpx` directly with no vendor SDK: `FireworksProvider`, `TogetherProvider`, `XaiProvider`. `AzureProvider` uses `urllib.request` against Azure AI Model Inference.

Whatever the style, the output is the same `ChatCompletionResponse`, so callers never see the difference.

## Supported providers

20+ providers ship today, including OpenAI, Anthropic, AWS Bedrock, Azure, Google, Mistral, Cohere, Groq, Cerebras, Hugging Face, WatsonX, Together, Fireworks, xAI, SambaNova, Nebius, OpenRouter, DeepSeek, Inception, Deepgram (audio), Ollama, and LM Studio. The complete table — with class names, SDKs, and the `pip` extra each needs — is in [reference/providers.md](../reference/providers.md).

## Parameter and response normalization

The framework layer (`aisuite/framework/`) defines the normalized types every provider targets:

- **`ChatCompletionResponse`** — `choices` (a list of `Choice`) and `usage`.
- **`Choice`** — `finish_reason`, `message`, and `intermediate_messages`.
- **`Message`** — `role`, `content`, `tool_calls`, `reasoning_content`, `refusal`.
- **`CompletionUsage`** — `prompt_tokens`, `completion_tokens`, `total_tokens`, plus optional `*_details` breakdowns (cached tokens, reasoning tokens, audio tokens).

For audio, a `ParameterMapper` and `ParamValidator` translate unified transcription options into each provider's parameters; see [the client reference](../reference/client-api.md#audio-transcription).

## Adding a provider

Because discovery is convention-based, adding a provider is small:

1. Create `aisuite/providers/<name>_provider.py`.
2. Define `class <Name>Provider(Provider)` implementing `chat_completions_create`.
3. Normalize the vendor response into a `ChatCompletionResponse`.
4. (If it needs an SDK) add the optional dependency and an extra in `pyproject.toml`.

Step-by-step in [guides/add-a-provider.md](../guides/add-a-provider.md).

## Related

- [Chat Completions](chat-completions.md) — how routing fits the call flow.
- [reference/providers.md](../reference/providers.md) — the full provider table.
- [ADR 0001](../architecture/adr/0001-provider-naming-convention.md) — why discovery is convention-based.
