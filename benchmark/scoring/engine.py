from __future__ import annotations

from statistics import mean

from benchmark.core.models import ModelBenchmarkResult, ModelCandidate, TaskResult


def normalize_speed(tps: float, ttft: float) -> float:
    if tps <= 0:
        return 0.0
    speed_component = min(tps / 80.0, 1.0)
    ttft_component = max(0.0, 1.0 - min(ttft / 10.0, 1.0))
    return (speed_component * 0.6) + (ttft_component * 0.4)


class ScoreEngine:
    def __init__(self, weights: dict[str, float]) -> None:
        self.weights = weights

    def score(self, candidate: ModelCandidate, task_results: list[TaskResult], metrics: dict[str, float]) -> ModelBenchmarkResult:
        correctness = mean(task.correctness for task in task_results)
        success_rate = mean(task.success_rate for task in task_results)
        context_score = mean(task.context_score for task in task_results)
        stability = mean(task.stability for task in task_results)
        speed_score = normalize_speed(metrics["tps"], metrics["ttft"])
        final_score = (
            self.weights["correctness"] * correctness
            + self.weights["speed"] * speed_score
            + self.weights["context_performance"] * context_score
            + self.weights["stability"] * stability
        )
        final_score = final_score * 0.85 + min(1.0, candidate.llmfit_score) * 0.15
        return ModelBenchmarkResult(
            model=candidate.name,
            fit=candidate.fit,
            llmfit_score=candidate.llmfit_score,
            categories=candidate.source_use_cases,
            tps=metrics["tps"],
            ttft=metrics["ttft"],
            success_rate=success_rate,
            stability=stability,
            context_score=context_score,
            correctness=correctness,
            speed_score=speed_score,
            final_score=final_score,
            task_results=task_results,
            raw_metrics=metrics,
        )
