from __future__ import annotations

from benchmark.core.models import InvocationMetrics, TaskResult
from benchmark.runners.ollama import OllamaRunner
from benchmark.tasks.base import BenchmarkTask

SAMPLE_CODE = """def normalize_names(items):
    result = []
    for item in items:
        if item is None:
            continue
        result.append(item.strip().lower())
    return result
"""

PROMPT = """You are editing a Python utility for an aider workflow.
Refactor the function below so it returns a sorted list of unique normalized names,
preserves insertion order before sorting for dedupe correctness, and adds type hints.
Return only the updated Python code.

```python
{code}
```
"""


class CodeEditTask(BenchmarkTask):
    name = "code_edit"
    category = "coding"

    def run(self, model: str, runner: OllamaRunner) -> tuple[TaskResult, list[InvocationMetrics]]:
        metrics = runner.invoke(model, PROMPT.format(code=SAMPLE_CODE))
        text = metrics.output_text.lower()
        correctness = sum([
            "sorted(" in text or ".sort(" in text,
            "set(" in text or "seen" in text,
            "-> list[str]" in text or "list[str]" in text,
            "def normalize_names" in text,
        ]) / 4
        success_rate = 1.0 if metrics.success and correctness >= 0.5 else 0.0
        task = TaskResult(
            task_name=self.name,
            category=self.category,
            success_rate=success_rate,
            correctness=correctness,
            context_score=correctness,
            stability=1.0 if metrics.success else 0.0,
            speed_score=metrics.tokens_per_second,
            raw={"output_preview": metrics.output_text[:300]},
        )
        return task, [metrics]
