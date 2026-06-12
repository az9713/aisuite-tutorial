# ADR 0001: Convention-based provider discovery

**Status:** Accepted

## Context

aisuite must support many LLM providers and make adding new ones cheap, including by external contributors. The question was how a provider key in a model string (`openai:gpt-4o`) gets resolved to the code that handles it.

Constraints:
- Adding a provider should be a small, self-contained change with no edits to shared files (which cause merge conflicts in a high-contribution repo).
- The supported-provider list should never drift out of sync with the code that actually exists.
- Provider SDKs are heavy and optional — they must not all be imported eagerly.

## Decision

Discover providers by **naming convention**. A provider key `<name>` resolves to module `aisuite/providers/<name>_provider.py` and class `<Name>Provider` (capitalized key + `Provider`). `ProviderFactory.create_provider` imports the module with `importlib` and instantiates the class; `get_supported_providers()` globs `providers/*_provider.py` and returns the stems. There is no central registry list.

## Alternatives considered

### Option A: A central registry dict
A `PROVIDERS = {"openai": OpenaiProvider, ...}` mapping.
- **Pros:** explicit; easy to read the full list in one place.
- **Cons:** every new provider edits the shared dict (merge conflicts); importing the module to reference the class forces eager imports of all SDKs; the list can drift from reality.

### Option B: Entry-point plugins (setuptools entry points)
Register providers via packaging metadata.
- **Pros:** allows out-of-tree providers.
- **Cons:** heavy machinery for what is mostly in-tree; harder to contribute (touch packaging config); discovery depends on install state.

### Option C: Convention-based discovery (chosen)
Filename + class-name convention, globbed at runtime.

## Rationale

Convention discovery makes "add a provider" equal to "add one file" — no shared-file edits, no merge conflicts, and the supported set is literally the files present, so it can't drift. Combined with lazy, cached instantiation, optional SDKs are imported only when a provider is actually used. The small cost — a key must match a filename — is documented and enforced by a clear `ValueError`.

## Trade-offs

- The link between key and code is implicit; a typo in the filename or class name fails at runtime rather than being caught statically.
- `get_supported_providers()` is filesystem-dependent and cached with `functools.cache`, so adding a file mid-process requires a restart to be seen.
- Out-of-tree providers aren't supported without dropping a file into the package directory.

## Consequences

- Contributing a provider is a one-file PR plus a `pyproject.toml` extra if it needs an SDK.
- Error messages list the discovered set, so a bad key is self-diagnosing.
- The [add-a-provider guide](../../guides/add-a-provider.md) is short because the mechanism is simple.
