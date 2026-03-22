# kortex

A local **mini-Codex** prototype with a Textual-based terminal UI and explicit human-in-the-loop checkpoints.

## Features

- Natural-language request input.
- Task planning with a user-editable approval step.
- Patch generation in strict JSON format.
- Diff review before any file is written.
- Validation after apply, with retry / skip / abort / continue decisions.
- Stateful execution loop that tracks tasks, attempts, last patch, and last error.

## Project structure

```text
.
├── main.py
├── pyproject.toml
└── core/
    ├── __init__.py
    ├── applier.py
    ├── builder.py
    ├── llm.py
    ├── loop.py
    ├── planner.py
    └── validator.py
```

## Run

1. Create a virtual environment.
2. Install dependencies.
3. Launch the TUI.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python main.py
```

## How it works

1. Enter a natural-language request in the input panel.
2. Press **Plan**.
3. Approve or edit the task list in the task approval dialog.
4. Press **Start**.
5. Review each generated diff and choose **Accept**, **Regenerate**, or **Reject**.
6. After validation, choose **Continue**, **Retry**, **Skip**, or **Abort**.

## Notes

- The included `LocalLLM` is intentionally deterministic and offline-safe.
- Validation uses `compileall` so the project remains easy to run locally.
- Generated edits are written relative to the current working directory.
