from __future__ import annotations

from dataclasses import dataclass, field

from core.llm import LocalLLM


@dataclass
class Planner:
    llm: LocalLLM = field(default_factory=LocalLLM)

    def create_tasks(self, request: str) -> list[str]:
        return self.llm.create_plan(request)
