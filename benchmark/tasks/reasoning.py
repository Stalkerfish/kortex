from __future__ import annotations

from benchmark.core.models import TaskResult
from benchmark.runners.ollama import OllamaRunner
from benchmark.tasks.base import BenchmarkTask

PROMPT = """Design an incremental migration plan for moving a monolithic Python service to a local-first,
Ollama-backed coding assistant platform used by 20 developers. Include architecture, rollout phases,
risk controls, observability, and rollback strategy. Use clear headings and numbered steps.
"""


class ReasoningTask(BenchmarkTask):
    name = "reasoning"
    category = "reasoning"

    def run(self, model: str, runner: OllamaRunner):
        metrics = runner.invoke(model, PROMPT)
        text = metrics.output_text
        headings = sum(1 for line in text.splitlines() if line.strip().startswith(("#", "1.", "2.", "3.")))
        keywords = ["architecture", "rollout", "risk", "observability", "rollback"]
        keyword_hits = sum(1 for word in keywords if word in text.lower())
        correctness = min(1.0, (headings / 4 + keyword_hits / len(keywords)) / 2)
        stability = 1.0 if metrics.success and len(text.split()) > 120 else 0.4 if metrics.success else 0.0
        task = TaskResult(
            task_name=self.name,
            category=self.category,
            success_rate=1.0 if metrics.success else 0.0,
            correctness=correctness,
            context_score=correctness,
            stability=stability,
            speed_score=metrics.tokens_per_second,
            raw={"word_count": len(text.split())},
        )
        return task, [metrics]
