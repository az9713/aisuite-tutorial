# Reference: Configuration and environment

How to configure aisuite: provider credentials, installable extras, and the default file locations.

## Provider credentials

Two ways to supply credentials; environment variables are the default.

### Environment variables

Read automatically by each provider when not passed in code. Copy the repo's `.env.sample` to `.env` and fill in what you use.

| Variable | Provider |
|----------|----------|
| `OPENAI_API_KEY` | OpenAI |
| `ANTHROPIC_API_KEY` | Anthropic |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` | AWS Bedrock |
| `AZURE_API_KEY` | Azure |
| `CEREBRAS_API_KEY` | Cerebras |
| `GOOGLE_APPLICATION_CREDENTIALS`, `GOOGLE_PROJECT_ID`, `GOOGLE_REGION` | Google Vertex |
| `HF_TOKEN` | Hugging Face |
| `FIREWORKS_API_KEY` | Fireworks |
| `MISTRAL_API_KEY` | Mistral |
| `TOGETHER_API_KEY` | Together |
| `WATSONX_API_KEY`, `WATSONX_SERVICE_URL`, `WATSONX_PROJECT_ID` | WatsonX |
| `XAI_API_KEY` | xAI |
| `SAMBANOVA_API_KEY` | SambaNova |
| `INCEPTION_API_KEY` | Inception |
| `OPENROUTER_API_KEY` | OpenRouter |

Ollama and LM Studio need no key (local servers).

### In code

Pass a `provider_configs` dict to the `Client`:

```python
ai.Client({
    "openai": {"api_key": "sk-..."},
    "aws": {"aws_access_key": "...", "aws_secret_key": "...", "aws_region": "us-west-2"},
})
```

The keys of `provider_configs` are provider keys; the values are forwarded to each provider's constructor.

## Client options

| Option | Values | Default | Effect |
|--------|--------|---------|--------|
| `extra_param_mode` | `strict` / `warn` / `permissive` | `warn` | How unknown audio-transcription parameters are handled (raise / warn / pass through). |

## Installable extras

```shell
pip install 'aisuite[<extra>]'
```

| Extra | Pulls in | For |
|-------|----------|-----|
| `anthropic` | `anthropic` | Anthropic provider |
| `aws` | `boto3` | AWS Bedrock |
| `azure` | — | Azure (no SDK) |
| `cerebras` | `cerebras_cloud_sdk` | Cerebras |
| `cohere` | `cohere` | Cohere |
| `deepgram` | `deepgram-sdk`, `soundfile`, `scipy`, `numpy` | Deepgram audio |
| `deepseek` | `openai` | DeepSeek |
| `google` | `vertexai`, `google-cloud-speech` | Google |
| `groq` | `groq` | Groq |
| `huggingface` | — | Hugging Face |
| `mistral` | `mistralai` | Mistral |
| `ollama` | `openai` | Ollama (local) |
| `lmstudio` | `openai` | LM Studio (local) |
| `openai` | `openai` | OpenAI + all OpenAI-compatible providers |
| `watsonx` | `ibm-watsonx-ai` | WatsonX |
| `mcp` | `mcp`, `nest-asyncio` | MCP tool support |
| `postgres` | `psycopg` | `PostgresStateStore` |
| `all` | all of the above | everything |

## Default file locations

aisuite writes runtime data under `.aisuite/` by default. Each is configurable.

| Path | Written by | Configurable via |
|------|-----------|------------------|
| `.aisuite/state/` | `FileStateStore` | `FileStateStore(root=...)` |
| `.aisuite/artifacts/` | `FileArtifactStore` | `FileArtifactStore(root=...)` |
| `.aisuite/events.jsonl` | `LocalTraceSink` / `JsonlTraceStore` | constructor `path=...` |
| `.aisuite/runs.jsonl` | `RunResult.write_trace_jsonl(path)` / the viewer's default | the `path` argument |

> **Tip:** Add `.aisuite/` to your `.gitignore` — it holds run state, artifacts, and traces, not source.

## Python and platform requirements

| Target | Requirement |
|--------|-------------|
| Library | Python 3.10+ |
| MCP (npx servers) | Node.js |
| Postgres store | a reachable PostgreSQL instance |

See [prerequisites](../getting-started/prerequisites.md) for component-specific needs (OpenCoworker, aisuite-js, viewer-ui).

## Related

- [reference/providers.md](providers.md) — the full provider table.
- [reference/client-api.md](client-api.md) — the `Client` constructor.
- [prerequisites](../getting-started/prerequisites.md)
