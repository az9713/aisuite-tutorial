# Toolkits

Toolkits are prebuilt, sandboxed tool families you attach to an agent. Each factory returns a list of callables ready to drop into `tools=[...]`. Three ship in the box: `files`, `git`, `shell`.

## What they are and why they're sandboxed

A toolkit gives a model real capabilities — reading files, running shell commands — without giving it the run of your machine. Every toolkit confines itself to a configured **root** (or working directory) and refuses any path that escapes it, raising `PermissionError`. Risky tools are marked with `ToolMetadata` so a [tool policy](tool-policies.md) can gate them.

Import them from `ai.toolkits`:

```python
import aisuite as ai
tools = [*ai.toolkits.files(root="."), *ai.toolkits.git(root=".")]
```

## files

`ai.toolkits.files(...)` exposes filesystem tools scoped to one or more roots.

```python
ai.toolkits.files(
    root=".",            # single-root convenience (mutually exclusive with roots)
    roots=None,          # multi-root: [{"path": ..., "writable": bool}, ...]
    allow_write=False,   # enable write tools in single-root mode
    max_read_bytes=200_000,
    max_search_bytes=1_000_000,
    ignore=None,         # glob patterns to skip (defaults below)
)
```

**Read tools (always present):**

| Tool | Risk | Returns |
|------|------|---------|
| `list_files(path=".", pattern="*", recursive=True, max_results=100)` | low | list of paths |
| `read_file(path)` | low | UTF-8 text (capped at `max_read_bytes`) |
| `read_file_lines(path, start_line=1, max_lines=100)` | low | a line range with metadata |
| `search_files(query, path=".", pattern="*", max_results=50)` | low | matches as `{path, line, text}` |

**Write tools (present when `allow_write=True`, or a root is marked writable):**

| Tool | Risk | Approval | Does |
|------|------|----------|------|
| `write_file(path, content, overwrite=True)` | medium | required | write a file |
| `apply_unified_diff(diff)` | medium | required | apply a unified diff |
| `apply_patch(patch)` | medium | required | apply a Codex-style `*** Begin Patch` envelope |
| `replace_in_file(path, old, new, expected_replacements=1)` | medium | required | exact-text replacement |

Default ignored directories: `.git`, `.venv`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `node_modules`, `dist`, `build`.

**Multi-root mode** lets you grant read access broadly and write access narrowly:

```python
ai.toolkits.files(roots=[
    {"path": "/work/project", "writable": True},   # index 0 = primary root
    {"path": "/work/reference", "writable": False},
])
```

## git

`ai.toolkits.git(root=..., max_output_chars=20000)` exposes read-only repository inspection:

| Tool | Risk | Does |
|------|------|------|
| `git_status()` | low | `git status --short --branch` |
| `git_diff(path=None, staged=False)` | low | `git diff`, optionally `--staged` or for one path |

Each returns `{command, exit_code, stdout, stderr, truncated}`, with output clipped to `max_output_chars`. There are no write operations — the git toolkit never commits, pushes, or checks out.

## shell

`ai.toolkits.shell(...)` exposes a single, deliberately dangerous tool:

```python
ai.toolkits.shell(
    cwd=".",                  # working directory (must exist)
    allowed_commands=None,    # allowlist; required unless allow_all=True
    allow_all=False,          # permit any command
    allow_shell=False,        # permit pipes/redirects/etc.
    default_timeout_seconds=30,
    max_output_chars=20_000,
)
```

| Tool | Risk | Approval |
|------|------|----------|
| `run_shell(command, timeout_seconds=None)` | high | required |

Two safety layers beyond approval:

- **Command allowlist.** You must pass `allowed_commands` or set `allow_all=True`. A command not on the list is rejected.
- **Shell-syntax blocking.** With `allow_shell=False` (the default), tokens like `|`, `&&`, `;`, `>`, `<`, and `2>` are forbidden — the command is parsed with `shlex.split`, not run through a shell — so a model can't chain or redirect its way out of the sandbox. Set `allow_shell=True` only when you intend to permit full shell syntax.

`run_shell` returns `{command, cwd, exit_code, stdout, stderr, timed_out}`.

## Risk levels at a glance

| Toolkit | Tool | Risk | Requires approval |
|---------|------|------|-------------------|
| files | read/list/search | low | no |
| files | write/diff/patch/replace | medium | yes |
| git | status/diff | low | no |
| shell | run_shell | high | yes |

These metadata are what [tool policies](tool-policies.md) read. Attaching a `RequireApprovalPolicy` is what actually enforces the approvals; the metadata only declares intent.

## Related

- [Tool policies](tool-policies.md) — turning `requires_approval` into an enforced gate.
- [The Agents API](agents-api.md) — attaching toolkits to an agent.
- [reference/toolkits.md](../reference/toolkits.md) — every parameter and return shape.
