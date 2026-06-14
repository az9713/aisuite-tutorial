"""
Research Desk - multi-provider, multi-agent CLI with persistent memory.

A lead `desk` agent coordinates four specialists:
    planner    -> breaks the request into steps
    researcher -> gathers findings from the notes folder
    critic     -> verifies those findings against the notes
    writer     -> produces the final answer

Usage:
    python desk.py           # start or resume conversation
    python desk.py --reset   # clear saved state and start fresh

Drop any .txt or .md files into the notes/ folder and the researcher
and critic sub-agents will be able to search and read them.
"""
import argparse
import os
import sys
from pathlib import Path

# Running `python path/to/desk.py` puts THIS file's folder on sys.path, not the
# repo root - so `import aisuite` (which lives at the repo root and isn't pip-
# installed) fails. Walk up to find the folder holding the aisuite package and
# add it, so the script runs from any working directory.
_HERE = Path(__file__).resolve().parent
for _root in (_HERE, *_HERE.parents):
    if (_root / "aisuite" / "__init__.py").exists():
        sys.path.insert(0, str(_root))
        break

import aisuite as ai

HERE = _HERE
NOTES_DIR = HERE / "notes"
STATE_DIR = HERE / ".aisuite" / "state"
THREAD_ID = "research-desk"


def load_env_files() -> None:
    """Load KEY=value pairs from .env into os.environ, if present.

    Looks next to this script and in the current working directory, so it works
    whether .env sits in the project folder or the repo root. A variable already
    set in the real environment wins (we never overwrite it).
    """
    for path in (HERE / ".env", Path.cwd() / ".env"):
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

PROVIDER_MENU = [
    ("openai",     "openai:gpt-4o-mini",          "OPENAI_API_KEY"),
    ("anthropic",  "anthropic:claude-sonnet-4-6",  "ANTHROPIC_API_KEY"),
    ("google",     "google:gemini-2.0-flash",      "GOOGLE_API_KEY"),
    ("openrouter", None,                           "OPENROUTER_API_KEY"),
]

OPENROUTER_PRESETS = [
    ("meta-llama/llama-3.3-70b-instruct", "Llama 3.3 70B"),
    ("google/gemini-2.0-flash-001",        "Gemini 2.0 Flash (via OR)"),
    ("deepseek/deepseek-r1",               "DeepSeek R1"),
    ("anthropic/claude-sonnet-4-5",        "Claude Sonnet (via OR)"),
    ("openai/gpt-4o",                      "GPT-4o (via OR)"),
]


def pick_model() -> str:
    print("\nChoose a provider:")
    for i, (name, default_model, _) in enumerate(PROVIDER_MENU, 1):
        label = default_model or "you choose the model"
        print(f"  {i}. {name:<12}  {label}")
    raw = input("-> ").strip()
    idx = int(raw) - 1 if raw.isdigit() else -1
    if not (0 <= idx < len(PROVIDER_MENU)):
        print("Invalid - defaulting to openai:gpt-4o.")
        return "openai:gpt-4o"

    provider_name, default_model, _ = PROVIDER_MENU[idx]
    if provider_name != "openrouter":
        return default_model

    print("\nOpenRouter model presets (or type any full model ID):")
    for i, (mid, label) in enumerate(OPENROUTER_PRESETS, 1):
        print(f"  {i}. {label:<35}  {mid}")
    raw = input("-> ").strip()
    if raw.isdigit() and 1 <= int(raw) <= len(OPENROUTER_PRESETS):
        return f"openrouter:{OPENROUTER_PRESETS[int(raw) - 1][0]}"
    return f"openrouter:{raw}" if raw else f"openrouter:{OPENROUTER_PRESETS[0][0]}"


def build_lead(model: str) -> ai.Agent:
    # Planner: decomposes the request. Reasons from the prompt alone - no tools.
    planner = ai.Agent(
        name="planner",
        model=model,
        instructions=(
            "Break the user's request into a short, ordered list of concrete "
            "research steps (2-5 items). Output only the numbered steps."
        ),
    )

    # Researcher: gathers facts from the notes. Read-only file access.
    researcher = ai.Agent(
        name="researcher",
        model=model,
        instructions=(
            "You answer questions from a folder of notes. Your file tools are "
            "rooted directly AT that folder, so start by calling list_files() "
            "with no arguments to see what's available, then read_file(path=NAME) "
            "using just the file name. Never prefix a path with 'notes/'. "
            "Quote the file name when you cite content. Report raw findings, "
            "not a polished write-up."
        ),
        tools=[*ai.toolkits.files(root=str(NOTES_DIR))],
    )

    # Critic: a second pair of eyes - re-reads the notes to check the findings.
    critic = ai.Agent(
        name="critic",
        model=model,
        instructions=(
            "You verify research findings against the source files. Your file "
            "tools are rooted directly AT the notes folder: call list_files() "
            "with no arguments, then read_file(path=NAME) using just the file "
            "name (never prefix with 'notes/'). Re-read the relevant files and "
            "flag any claim that is unsupported, missing a citation, or "
            "contradicted. If everything checks out, say so plainly."
        ),
        tools=[*ai.toolkits.files(root=str(NOTES_DIR))],
    )

    # Writer: turns verified findings into the deliverable. No tools - pure prose.
    writer = ai.Agent(
        name="writer",
        model=model,
        instructions=(
            "Turn the provided findings into a clear, well-structured answer for "
            "the user. Be concise and preserve any file citations you are given."
        ),
    )

    return ai.Agent(
        name="desk",
        model=model,
        instructions=(
            "You are a research desk that coordinates a team of specialist agents. "
            "For a substantive request, work in this order:\n"
            "1. Call `planner` to break the request into steps.\n"
            "2. Call `researcher` to gather findings from the notes.\n"
            "3. Call `critic` to verify those findings against the notes.\n"
            "4. Call `writer` to produce the final answer from the verified findings.\n"
            "Skip steps that don't apply (e.g. a simple greeting needs none). "
            "Return the writer's output as your reply."
        ),
        tools=[
            ai.agent_tool(
                planner,
                description="Break a request into an ordered list of research steps.",
            ),
            ai.agent_tool(
                researcher,
                description="Search and read the notes folder; return raw findings.",
            ),
            ai.agent_tool(
                critic,
                description="Verify findings against the notes; flag unsupported claims.",
            ),
            ai.agent_tool(
                writer,
                description="Turn verified findings into the final user-facing answer.",
            ),
        ],
    )


def print_turn_trace(result: ai.RunResult, verbose: bool = False) -> None:
    """Show which sub-agents the lead called this turn.

    Compact mode prints a one-line hand-off chain (planner -> researcher -> ...).
    Verbose mode (--trace) dumps the full step list via aisuite's print_trace.
    """
    if verbose:
        # Print the step list only — NOT the final output, which is shown once
        # below under "desk>". (result.print_trace() would duplicate the answer.)
        print("  [trace]")
        for step in result.steps:
            name = step.name or "-"
            bits = []
            if step.data.get("allowed") is not None:
                bits.append(f"allowed={step.data['allowed']}")
            if step.data.get("status"):
                bits.append(f"status={step.data['status']}")
            suffix = f" ({', '.join(bits)})" if bits else ""
            print(f"    - {step.type}: {name}{suffix}")
        return
    calls = [
        step.name
        for step in result.steps
        if step.type == "tool_call" and step.name
    ]
    if calls:
        print("  [team] " + " -> ".join(calls))


def main() -> None:
    load_env_files()

    parser = argparse.ArgumentParser(description="Research Desk")
    parser.add_argument("--reset", action="store_true", help="Clear saved conversation")
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Print the full step trace each turn (default: a one-line hand-off chain)",
    )
    args = parser.parse_args()

    store = ai.FileStateStore(root=str(STATE_DIR))

    if args.reset:
        store.delete_state(THREAD_ID)
        print("Conversation cleared.\n")

    stored = store.load_state(THREAD_ID)
    if stored:
        model = stored.state.metadata.get("model", "openai:gpt-4o")
        print(f"Resuming conversation (revision {stored.revision}, model: {model}).")
        print("Type 'quit' or run with --reset to start fresh.\n")
        is_new = False
    else:
        print("Research Desk - new conversation.")
        model = pick_model()
        print(f"\nModel: {model}\n")
        is_new = True

    agent = build_lead(model)

    try:
        while True:
            try:
                prompt = input("you> ").strip()
            except EOFError:
                break
            if not prompt or prompt.lower() in ("quit", "exit", "q"):
                break

            if is_new:
                result = ai.Runner.run_sync(
                    agent,
                    prompt,
                    max_turns=12,
                    state_store=store,
                    thread_id=THREAD_ID,
                    metadata={"model": model},
                )
                is_new = False
            else:
                result = ai.Runner.continue_sync(
                    agent,
                    prompt,
                    max_turns=12,
                    state_store=store,
                    thread_id=THREAD_ID,
                )

            print_turn_trace(result, verbose=args.trace)
            print(f"\ndesk> {result.final_output}\n")

    except KeyboardInterrupt:
        print("\nbye.")


if __name__ == "__main__":
    main()
