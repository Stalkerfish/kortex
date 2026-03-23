from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ModelCandidate:
    name: str
    fit: str = "unknown"
    llmfit_score: float = 0.0
    source_use_cases: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PromptTurn:
    role: str
    content: str


@dataclass(slots=True)
class InvocationMetrics:
    latency_seconds: float
    ttft_seconds: float
    tokens_per_second: float
    output_tokens: int
    output_text: str
    success: bool
    error: str | None = None


@dataclass(slots=True)
class TaskResult:
    task_name: str
    category: str
    success_rate: float
    correctness: float
    context_score: float
    stability: float
    speed_score: float
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ModelBenchmarkResult:
    model: str
    fit: str
    llmfit_score: float
    categories: list[str]
    tps: float
    ttft: float
    success_rate: float
    stability: float
    context_score: float
    correctness: float
    speed_score: float
    final_score: float
    task_results: list[TaskResult] = field(default_factory=list)
    raw_metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["task_results"] = [asdict(task) for task in self.task_results]
        return payload


@dataclass(slots=True)
class BenchmarkConfig:
    use_cases: list[str]
    output_dir: Path
    cache_dir: Path
    max_models: int = 5
    parallelism: int = 1
    iterations: int = 1
    ollama_binary: str = "ollama"
    llmfit_binary: str = "llmfit"
    weights: dict[str, float] = field(
        default_factory=lambda: {
            "correctness": 0.4,
            "speed": 0.2,
            "context_performance": 0.2,
            "stability": 0.2,
        }
    )
    task_settings: dict[str, Any] = field(default_factory=dict)
    runner: dict[str, Any] = field(default_factory=dict)
