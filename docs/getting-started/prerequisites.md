# Prerequisites

What you need before running aisuite. The quickstarts link here so there are no surprises mid-setup.

## For the Python library

### Python 3.10+
Verify: `python --version` (should print `Python 3.10.x` or higher).
Install: [python.org/downloads](https://www.python.org/downloads/)

### pip (or Poetry for development)
The package installs with pip. Contributors use [Poetry](https://python-poetry.org/) — the repo ships a `pyproject.toml` and `poetry.lock`.

### Provider SDKs (optional extras)
The base `aisuite` package has no provider SDKs. Install the extras for the providers you call:

```shell
pip install aisuite               # base, no provider SDKs
pip install 'aisuite[anthropic]'  # one provider
pip install 'aisuite[all]'        # every provider SDK
```

Each provider maps to an extra. See [reference/providers.md](../reference/providers.md) for the full table. Optional feature extras: `mcp` (Model Context Protocol), `postgres` (the Postgres state store).

### API keys
You need a key only for the providers you actually call. Keys are read from environment variables by default, or passed to the `Client` constructor.

| Provider | Environment variable |
|----------|---------------------|
| OpenAI | `OPENAI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| AWS Bedrock | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` |
| Azure | `AZURE_API_KEY` |
| Cerebras | `CEREBRAS_API_KEY` |
| Google (Vertex) | `GOOGLE_APPLICATION_CREDENTIALS`, `GOOGLE_PROJECT_ID`, `GOOGLE_REGION` |
| Hugging Face | `HF_TOKEN` |
| Fireworks | `FIREWORKS_API_KEY` |
| Mistral | `MISTRAL_API_KEY` |
| Together | `TOGETHER_API_KEY` |
| WatsonX | `WATSONX_API_KEY`, `WATSONX_SERVICE_URL`, `WATSONX_PROJECT_ID` |
| xAI | `XAI_API_KEY` |
| SambaNova | `SAMBANOVA_API_KEY` |
| Inception | `INCEPTION_API_KEY` |
| OpenRouter | `OPENROUTER_API_KEY` |

The repo's `.env.sample` lists these; copy it to `.env` and fill in what you need. Per-provider key instructions live in [`guides/`](https://github.com/andrewyng/aisuite/tree/main/guides). Ollama and LM Studio need no key.

> **Tip:** Tools like [`python-dotenv`](https://pypi.org/project/python-dotenv/) or [`direnv`](https://direnv.net/) keep keys out of your shell history.

### For local models (no key)
Run fully local with [Ollama](https://ollama.com) or [LM Studio](https://lmstudio.ai/). Install the app, pull a model (`ollama pull llama3.3`), and use a model string like `ollama:llama3.3`.

## For MCP tools

### Node.js (for npx-based MCP servers)
Many MCP servers run via `npx`. Verify: `node --version` and `npx --version`.
Install: [nodejs.org](https://nodejs.org/)

Then install the aisuite MCP extra: `pip install 'aisuite[mcp]'`.

## For the Postgres state store

A reachable PostgreSQL instance and the extra: `pip install 'aisuite[postgres]'`. The store can create its own schema on first use.

## For OpenCoworker (desktop app)

| Platform | Requirement |
|----------|-------------|
| macOS | 13+ on Apple Silicon (M1 or later) |
| Windows | 10 or 11 (x64) |

No Python needed — the [installer](../opencoworker-quickstart.md) is self-contained. Bring your own API key, or run local with Ollama.

## For building components from source

| Component | Needs |
|-----------|-------|
| [OpenCoworker](../components/opencoworker.md) | Python 3.10+, Node.js (for the React GUI), optionally a Rust toolchain for the Tauri shell |
| [aisuite-js](../components/aisuite-js.md) | Node.js 16+ |
| [viewer-ui](../components/viewer-ui.md) | Node.js (Vite dev server) |

## Next

- [Chat Completions quickstart](../chat-completions-quickstart.md) — first completion.
- [Onboarding](onboarding.md) — the full conceptual walkthrough.
