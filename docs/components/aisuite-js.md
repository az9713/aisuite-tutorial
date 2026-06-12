# aisuite-js (TypeScript)

A TypeScript/JavaScript port of aisuite's Chat Completions layer — one unified client across providers, with OpenAI-format types. Source: [`aisuite-js/`](https://github.com/andrewyng/aisuite/tree/main/aisuite-js).

## What it is

The npm package `aisuite` (version 0.1.1). It ports the **Chat Completions API** — the same `provider:model` routing and OpenAI-shaped types as the Python library — to Node. It deliberately does **not** port the higher layers.

## What's included vs. not

| Feature | Python | aisuite-js |
|---------|--------|-----------|
| Chat completions, `provider:model` routing | ✅ | ✅ |
| Streaming (`AsyncIterable<ChatCompletionChunk>`) | ✅ | ✅ |
| Tool calling (pass tools, get tool-call requests) | ✅ | ✅ (manual handling) |
| Audio transcription (ASR) | ✅ | ✅ |
| Agents API (`Agent`, `Runner`, policies, state) | ✅ | ❌ |
| Toolkits (files/git/shell) | ✅ | ❌ |
| MCP | ✅ | ❌ |

If you need agents, toolkits, or MCP, use the Python library.

## Supported providers

OpenAI, Anthropic, Mistral, Groq, and Deepgram (ASR only). Each wraps the vendor's official JS SDK (`openai`, `@anthropic-ai/sdk`, `@mistralai/mistralai`, `groq-sdk`, `@deepgram/sdk`).

## Install

```bash
npm install aisuite
```

Tech: TypeScript 5+, Node 16+, ES modules.

## Usage

```typescript
import { Client } from "aisuite";

const client = new Client({
  openai: { apiKey: process.env.OPENAI_API_KEY },
  anthropic: { apiKey: process.env.ANTHROPIC_API_KEY },
});

const response = await client.chat.completions.create({
  model: "anthropic:claude-3-haiku-20240307",
  messages: [{ role: "user", content: "Hello" }],
  temperature: 0.7,
});
console.log(response.choices[0].message.content);
```

Streaming:

```typescript
const stream = await client.chat.completions.create({
  model: "openai:gpt-4o",
  messages: [{ role: "user", content: "Count to five." }],
  stream: true,
});
for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content ?? "");
}
```

Audio transcription:

```typescript
const result = await client.audio.transcriptions.create({
  model: "deepgram:nova-2",   // or "openai:whisper-1"
  file: audioBuffer,
  language: "en",
});
```

Helper methods on the client: `listProviders()`, `listASRProviders()`, `isProviderConfigured(name)`, `isASRProviderConfigured(name)`.

## Exports

```typescript
export { Client };
export * from "./types";
export * from "./core/errors";       // AISuiteError, ProviderNotConfiguredError
export { parseModel } from "./core/model-parser";
export { OpenAIProvider, AnthropicProvider, GroqProvider, MistralProvider };
export { DeepgramASRProvider };
```

## Project layout

```
aisuite-js/
├── src/
│   ├── index.ts            # exports
│   ├── client.ts           # Client class
│   ├── types.ts            # TS interfaces (OpenAI-shaped)
│   ├── core/               # base-provider, errors, model-parser
│   ├── providers/          # openai, anthropic, mistral, groq
│   └── asr-providers/      # deepgram
├── examples/               # basic-usage, tool-calling, streaming, mistral, groq, deepgram, openai-asr
└── tests/
```

## Build and test

```bash
npm run build          # tsc → dist/
npm test               # Jest
npm run test:examples  # run the bundled examples
npm run example:basic  # one example
npm run lint           # ESLint
npm run dev            # tsc --watch
```

## Related

- [Chat Completions concept](../concepts/chat-completions.md) — the Python equivalent.
- [What is aisuite?](../overview/what-is-this.md#what-aisuite-is-not) — why the JS port is chat-only.
