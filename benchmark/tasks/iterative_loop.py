from __future__ import annotations

from benchmark.core.models import PromptTurn, TaskResult
from benchmark.runners.ollama import OllamaRunner
from benchmark.tasks.base import BenchmarkTask

PROMPTS = [
    "Propose a file layout for a local LLM benchmark tool.",
    "Now add logging and caching concerns without changing the goals.",
    "Now adapt the plan for Ollama plus aider workflows.",
    "Finally summarize the final architecture in five bullets.",
]


class IterativeLoopTask(BenchmarkTask):
    name = "iterative_loop"
    category = "stability"

    def __init__(self, turns: int = 4) -> None:
        self.turns = turns

    def run(self, model: str, runner: OllamaRunner):
        history: list[PromptTurn] = []
        invocations = []
        consistency_hits = 0
        for prompt in PROMPTS[: self.turns]:
            metrics = runner.invoke(model, prompt, history)
            invocations.append(metrics)
            if any(token in metrics.output_text.lower() for token in ["ollama", "cache", "logging", "benchmark"]):
                consistency_hits += 1
            history.append(PromptTurn(role="user", content=prompt))
            history.append(PromptTurn(role="assistant", content=metrics.output_text[:1200]))
        stability = consistency_hits / max(1, len(invocations))
        success_rate = sum(1 for item in invocations if item.success) / max(1, len(invocations))
        avg_tps = sum(item.tokens_per_second for item in invocations) / max(1, len(invocations))
        task = TaskResult(
            task_name=self.name,
            category=self.category,
            success_rate=success_rate,
            correctness=stability,
            context_score=stability,
            stability=stability,
            speed_score=avg_tps,
            raw={"turns": len(invocations)},
        )
        return task, invocations
