from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from core.llm import LocalLLM


@dataclass
class Builder:
    workspace: Path
    llm: LocalLLM = field(default_factory=LocalLLM)

    def generate_patch(self, request: str, task: str, error: str | None = None) -> dict:
        raw = self.llm.regenerate_patch(request, task, self.workspace, error) if error else self.llm.build_patch(request, task, self.workspace)
        return json.loads(raw)
