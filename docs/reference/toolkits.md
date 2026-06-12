# Reference: Toolkits

The three built-in toolkits. Each factory returns a `list` of callable tools to spread into `tools=[...]`. Import from `aisuite.toolkits`.

## files

```python
ai.toolkits.files(*, root=None, roots=None, allow_write=False,
                  max_read_bytes=200_000, max_search_bytes=1_000_000, ignore=None)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `root` | str \| Path \| None | None | Single root directory. Mutually exclusive with `roots`. |
| `roots` | list \| None | None | Multi-root: list of `{"path": ..., "writable": bool}`. Index 0 is the primary root. |
| `allow_write` | bool | False | Enable write tools (single-root mode). |
| `max_read_bytes` | int | 200,000 | Max file size `read_file` will return. |
| `max_search_bytes` | int | 1,000,000 | Max bytes scanned per `search_files`. |
| `ignore` | list[str] \| None | see below | Glob patterns to skip. |

Default ignores: `.git`, `.venv`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `node_modules`, `dist`, `build`.

### Tools

| Tool | Signature | Risk | Approval | Returns |
|------|-----------|------|----------|---------|
| `list_files` | `(path=".", pattern="*", recursive=True, max_results=100)` | low | no | `list[str]` |
| `read_file` | `(path)` | low | no | `str` |
| `read_file_lines` | `(path, start_line=1, max_lines=100)` | low | no | `{path, start_line, end_line, total_lines, content}` |
| `search_files` | `(query, path=".", pattern="*", max_results=50)` | low | no | `list[{path, line, text}]` |
| `write_file` | `(path, content, overwrite=True)` | medium | yes | `str` (relative path) |
| `apply_unified_diff` | `(diff)` | medium | yes | `{changed_files, added_files, deleted_files, file_count, hunk_count}` |
| `apply_patch` | `(patch)` | medium | yes | same as `apply_unified_diff` (Codex `*** Begin Patch` envelope) |
| `replace_in_file` | `(path, old, new, expected_replacements=1)` | medium | yes | `{path, replacements, chars_before, chars_after}` |

Write tools appear only when `allow_write=True` or a root is marked `writable`. Every path is resolved against the configured root(s); a path escaping them raises `PermissionError`.

## git

```python
ai.toolkits.git(*, root, max_output_chars=20000)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `root` | str \| Path | — | Repository root (required). |
| `max_output_chars` | int | 20,000 | Output truncation limit. |

### Tools

| Tool | Signature | Risk | Returns |
|------|-----------|------|---------|
| `git_status` | `()` | low | `{command, exit_code, stdout, stderr, truncated}` (`git status --short --branch`) |
| `git_diff` | `(path=None, staged=False)` | low | same shape (`git diff` [`--staged`] [`-- path`]) |

Read-only — no commit, push, or checkout. Paths are confined to `root`.

## shell

```python
ai.toolkits.shell(*, cwd, allowed_commands=None, allow_all=False,
                  allow_shell=False, default_timeout_seconds=30, max_output_chars=20_000)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cwd` | str \| Path | — | Working directory (must exist). |
| `allowed_commands` | list[str] \| None | None | Command allowlist. Required unless `allow_all=True`. |
| `allow_all` | bool | False | Permit any command. |
| `allow_shell` | bool | False | Permit shell metacharacters (pipes, redirects, …). |
| `default_timeout_seconds` | int | 30 | Default per-command timeout. |
| `max_output_chars` | int | 20,000 | Output truncation limit. |

### Tools

| Tool | Signature | Risk | Approval | Returns |
|------|-----------|------|----------|---------|
| `run_shell` | `(command, timeout_seconds=None)` | high | yes | `{command, cwd, exit_code, stdout, stderr, timed_out}` |

Safety: you must pass `allowed_commands` or `allow_all=True`. With `allow_shell=False` (default) these tokens are rejected (parsed via `shlex.split`, not a shell): `|`, `||`, `&&`, `;`, `>`, `>>`, `<`, `<<`, `2>`, `2>>`.

## Risk and approval summary

| Toolkit | Tools | Risk | Approval |
|---------|-------|------|----------|
| files | read/list/search | low | no |
| files | write/diff/patch/replace | medium | yes |
| git | status/diff | low | no |
| shell | run_shell | high | yes |

Approval requirements are declared as `ToolMetadata`; enforce them by attaching a [policy](policies-and-stores.md).

## Related

- [Toolkits concept](../concepts/toolkits.md)
- [Tool policies](../concepts/tool-policies.md)
