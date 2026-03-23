from __future__ import annotations

from abc import ABC, abstractmethod

from benchmark.core.models import InvocationMetrics, TaskResult
from benchmark.runners.ollama import OllamaRunner


class BenchmarkTask(ABC):
    name: str
    category: str

    @abstractmethod
    def run(self, model: str, runner: OllamaRunner) -> tuple[TaskResult, list[InvocationMetrics]]:
        raise NotImplementedError
