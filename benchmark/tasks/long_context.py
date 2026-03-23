from __future__ import annotations

from benchmark.core.models import TaskResult
from benchmark.runners.ollama import OllamaRunner
from benchmark.tasks.base import BenchmarkTask

BASE = "Local benchmarking helps choose models for aider workflows by balancing speed, accuracy, and stability. "
QUESTION = "After reading the context, list the three primary evaluation dimensions and provide one sentence on why each matters."


class LongContextTask(BenchmarkTask):
    name = "long_context"
    category = "long_context"

    def __init__(self, repeat_factor: int = 180) -> None:
        self.repeat_factor = repeat_factor

    def run(self, model: str, runner: OllamaRunner):
        prompt = (BASE * self.repeat_factor) + "\n\n" + QUESTION
        metrics = runner.invoke(model, prompt)
        text = metrics.output_text.lower()
        hits = sum(1 for token in ["speed", "accuracy", "stability", "context"] if token in text)
        context_score = min(1.0, hits / 4)
        task = TaskResult(
            task_name=self.name,
            category=self.category,
            success_rate=1.0 if metrics.success else 0.0,
            correctness=context_score,
            context_score=context_score,
            stability=1.0 if metrics.success and len(metrics.output_text) > 40 else 0.0,
            speed_score=metrics.tokens_per_second,
            raw={"prompt_chars": len(prompt), "output_chars": len(metrics.output_text)},
        )
        return task, [metrics]
