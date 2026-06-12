# ADR 0002: Generate tool schemas from Python functions

**Status:** Accepted

## Context

To let a model call tools, providers need a JSON Schema for each tool — name, parameters, types, descriptions, required fields. The question was where that schema comes from.

Constraints:
- The information a schema needs (parameter names, types, descriptions) already exists in a typed, documented Python function.
- Schemas and implementations that are maintained separately drift apart, producing subtle, hard-to-debug failures (the model calls a parameter that the function renamed).
- Some users need full manual control of the tool loop and their own schemas.

## Decision

Treat the **Python function as the single source of truth**. The `Tools` class generates the OpenAI-format schema from the function: name from `__name__`, description from the docstring summary, parameters and types from the annotated signature, and parameter descriptions from the docstring's `Args:` section (parsed with `docstring_parser`). A Pydantic model derived from the signature validates the model's arguments before the function runs. Passing raw JSON specs remains supported for manual control.

## Alternatives considered

### Option A: Author JSON specs by hand
The caller writes the schema dict and pairs it with a function.
- **Pros:** total control over the schema; no inference magic.
- **Cons:** duplicates information already in the function; drifts on every refactor; verbose; error-prone.

### Option B: A decorator DSL describing parameters
A `@tool` decorator with explicit parameter declarations.
- **Pros:** explicit; decouples schema from signature.
- **Cons:** still duplicates the signature; another API to learn; the decorator and the function can disagree.

### Option C: Infer from the function (chosen)
Signature + docstring → schema, with raw specs as an escape hatch.

## Rationale

The function already encodes everything the schema needs, in a form the type checker and the reader both rely on. Inferring from it means the schema can't drift — refactor the function and the schema follows. Pydantic validation closes the loop on the input side: the model's arguments are checked against the same signature before your code sees them. Keeping raw-spec support means power users lose nothing. The one requirement — every parameter must be annotated — is reasonable in typed Python and fails loudly (`TypeError`) when violated.

## Trade-offs

- Functions must be fully annotated and documented to produce good schemas; a sparse docstring yields a sparse tool description the model may misuse.
- Inference is opinionated; exotic schema features (deeply nested `anyOf`, custom formats) are easier to express as raw specs than to coax from a signature. MCP tools sidestep this by preserving the server's exact schema on `__mcp_input_schema__`.

## Consequences

- Adding a tool is "write a documented function" — see [tool calling](../../concepts/tool-calling.md).
- Docstring quality directly affects tool-use quality, which is worth emphasizing in guides.
- The same generation path serves both the Chat Completions `tools=` parameter and the Agents API, so behavior is consistent across layers.
