# Reference: Providers

Every provider aisuite ships, its class, the `pip` extra it needs, and how to authenticate. Use the provider key as the prefix in a `provider:model` string.

## Provider table

| Key | Class | `pip` extra | SDK / mechanism | Auth (env var) |
|-----|-------|-------------|-----------------|----------------|
| `openai` | `OpenaiProvider` | `openai` | `openai` SDK | `OPENAI_API_KEY` |
| `anthropic` | `AnthropicProvider` | `anthropic` | `anthropic` SDK | `ANTHROPIC_API_KEY` |
| `aws` | `AwsProvider` | `aws` | `boto3` (Bedrock Converse) | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` |
| `azure` | `AzureProvider` | `azure` | `urllib` (Azure AI Model Inference) | `AZURE_API_KEY` |
| `cerebras` | `CerebrasProvider` | `cerebras` | `cerebras_cloud_sdk` | `CEREBRAS_API_KEY` |
| `cohere` | `CohereProvider` | `cohere` | `cohere` SDK | (Cohere key) |
| `deepgram` | `DeepgramProvider` | `deepgram` | `deepgram-sdk` (audio only) | (Deepgram key) |
| `deepseek` | `DeepseekProvider` | `deepseek` | `openai` SDK (custom base URL) | (DeepSeek key) |
| `fireworks` | `FireworksProvider` | — | `httpx` | `FIREWORKS_API_KEY` |
| `google` | `GoogleProvider` | `google` | `vertexai` / `google-cloud-speech` | `GOOGLE_APPLICATION_CREDENTIALS`, `GOOGLE_PROJECT_ID`, `GOOGLE_REGION` |
| `groq` | `GroqProvider` | `groq` | `groq` SDK | (Groq key) |
| `huggingface` | `HuggingfaceProvider` | `huggingface` | Inference API | `HF_TOKEN` |
| `inception` | `InceptionProvider` | — | `openai` SDK (custom base URL) | `INCEPTION_API_KEY` |
| `lmstudio` | `LmstudioProvider` | `lmstudio` | `openai` SDK (local server) | none (local) |
| `mistral` | `MistralProvider` | `mistral` | `mistralai` SDK | `MISTRAL_API_KEY` |
| `nebius` | `NebiusProvider` | — | `openai` SDK (custom base URL) | (Nebius key) |
| `ollama` | `OllamaProvider` | `ollama` | `openai` SDK (local server) | none (local) |
| `openrouter` | `OpenrouterProvider` | — | `openai` SDK (custom base URL) | `OPENROUTER_API_KEY` |
| `sambanova` | `SambanovaProvider` | — | `openai` SDK (custom base URL) | `SAMBANOVA_API_KEY` |
| `together` | `TogetherProvider` | — | `httpx` | `TOGETHER_API_KEY` |
| `watsonx` | `WatsonxProvider` | `watsonx` | `ibm-watsonx-ai` | `WATSONX_API_KEY`, `WATSONX_SERVICE_URL`, `WATSONX_PROJECT_ID` |
| `xai` | `XaiProvider` | — | `httpx` | `XAI_API_KEY` |

> **Note:** An em-dash in the extra column means the adapter needs no extra (it uses `httpx` or the `openai` SDK already pulled by another extra). Providers built on the `openai` SDK install via the `openai` extra (or `all`).

## Installing extras

```shell
pip install 'aisuite[anthropic]'        # one provider
pip install 'aisuite[anthropic,groq]'   # several
pip install 'aisuite[all]'              # every provider SDK
```

The `all` extra includes: `anthropic`, `aws` (boto3), `cerebras`, `google` (vertexai + cloud-speech), `groq`, `mistral`, `openai`, `cohere`, `watsonx`, `deepgram` (+ soundfile, scipy, numpy), `mcp` (+ nest-asyncio), and `postgres` (psycopg).

## Model string examples

| Provider | Example model string |
|----------|---------------------|
| OpenAI | `openai:gpt-4o` |
| Anthropic | `anthropic:claude-sonnet-4-6` |
| Google | `google:gemini-1.5-pro` |
| AWS Bedrock | `aws:anthropic.claude-3-5-sonnet-20240620-v1:0` |
| Ollama (local) | `ollama:llama3.3` |
| Groq | `groq:llama-3.1-70b-versatile` |
| Deepgram (audio) | `deepgram:nova-2` |

The model name after the colon is passed through to the provider unchanged; consult the provider's own model list for valid names.

## Per-provider key instructions

Step-by-step instructions for obtaining a key for each provider live in the repo's [`guides/`](https://github.com/andrewyng/aisuite/tree/main/guides) directory (Anthropic, AWS, Azure, Cohere, Google, Hugging Face, Mistral, OpenAI, SambaNova, xAI, DeepSeek, Ollama, LM Studio).

## Adding a provider

See [guides/add-a-provider.md](../guides/add-a-provider.md) and [the providers concept](../concepts/providers.md).

## Related

- [Providers concept](../concepts/providers.md)
- [reference/configuration.md](configuration.md) — environment variables and extras.
