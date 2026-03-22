from __future__ import annotations

import difflib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Applier:
    workspace: Path

    def diff_from_patch(self, patch: dict) -> str:
        rendered: list[str] = []
        for edit in patch.get("edits", []):
            file_path = self.workspace / edit["file"]
            before = file_path.read_text() if file_path.exists() else ""
            after = edit["content"]
            diff = difflib.unified_diff(
                before.splitlines(),
                after.splitlines(),
                fromfile=str(edit["file"]),
                tofile=str(edit["file"]),
                lineterm="",
            )
            rendered.append("\n".join(diff) or f"No changes for {edit['file']}")
        return "\n\n".join(rendered)

    def apply(self, patch: dict) -> None:
        for edit in patch.get("edits", []):
            file_path = self.workspace / edit["file"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(edit["content"])
