from __future__ import annotations

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from statistics import mean

from benchmark.core.ui import Console
from benchmark.core.ui import Table

from benchmark.core.cache import ResultCache
from benchmark.core.models import BenchmarkConfig, InvocationMetrics, ModelBenchmarkResult
from benchmark.runners.llmfit import LLMFitRunner, merge_candidates
from benchmark.runners.ollama import OllamaRunner
from benchmark.scoring.engine import ScoreEngine
from benchmark.tasks import build_tasks

LOGGER = logging.getLogger(__name__)


class BenchmarkOrchestrator:
    def __init__(self, config: BenchmarkConfig) -> None:
        self.config = config
        self.cache = ResultCache(config.cache_dir)
        self.console = Console()

    def list_candidates(self) -> list[dict]:
        llmfit = LLMFitRunner(self.config.llmfit_binary)
        raw = []
        for use_case in self.config.use_cases:
            raw.extend(llmfit.recommend(use_case))
        merged = merge_candidates(raw, self.config.max_models)
        return [candidate.__dict__ for candidate in merged]

    def run(self) -> tuple[list[ModelBenchmarkResult], Path]:
        llmfit = LLMFitRunner(self.config.llmfit_binary)
        raw_candidates = []
        for use_case in self.config.use_cases:
            raw_candidates.extend(llmfit.recommend(use_case))
        candidates = merge_candidates(raw_candidates, self.config.max_models)
        tasks = build_tasks(self.config.task_settings)
        runner = OllamaRunner(
            binary=self.config.ollama_binary,
            timeout_seconds=int(self.config.runner.get("timeout_seconds", 180)),
            env=self.config.runner.get("env") or None,
        )
        scorer = ScoreEngine(self.config.weights)

        results = []
        for candidate in candidates:
            LOGGER.info("Benchmarking %s", candidate.name)
            task_results = []
            invocations: list[InvocationMetrics] = []
            for task in tasks:
                cache_key = {
                    "model": candidate.name,
                    "task": task.name,
                    "settings": self.config.task_settings.get(task.name, {}),
                }
                cached = self.cache.load(cache_key)
                if cached:
                    task_results.append(self._task_result_from_dict(cached["task_result"]))
                    invocations.extend(self._metric_list_from_dicts(cached["invocations"]))
                    continue
                task_result, task_invocations = task.run(candidate.name, runner)
                task_results.append(task_result)
                invocations.extend(task_invocations)
                self.cache.save(
                    cache_key,
                    {
                        "task_result": task_result.__dict__,
                        "invocations": [item.__dict__ for item in task_invocations],
                    },
                )
            agg = self._aggregate_invocations(invocations)
            results.append(scorer.score(candidate, task_results, agg))

        results.sort(key=lambda item: item.final_score, reverse=True)
        run_dir = self._write_outputs(results)
        self.print_table(results)
        return results, run_dir

    def compare(self, models: list[str]) -> list[dict]:
        latest = self._latest_run_dir()
        payload = json.loads((latest / "scoreboard.json").read_text())
        return [item for item in payload if item["model"] in models]

    def top(self, category: str | None = None, limit: int = 5) -> list[dict]:
        latest = self._latest_run_dir()
        payload = json.loads((latest / "scoreboard.json").read_text())
        items = payload
        if category:
            items = [item for item in items if category in item["categories"] or any(t["category"] == category for t in item["task_results"])]
        return items[:limit]

    def print_table(self, results: list[ModelBenchmarkResult]) -> None:
        table = Table(title="Local LLM Scoreboard")
        for column in ["Rank", "Model", "Fit", "Score", "TPS", "TTFT", "Success", "Stability"]:
            table.add_column(column)
        for idx, result in enumerate(results, start=1):
            table.add_row(
                str(idx),
                result.model,
                result.fit,
                f"{result.final_score:.3f}",
                f"{result.tps:.1f}",
                f"{result.ttft:.2f}s",
                f"{result.success_rate:.2%}",
                f"{result.stability:.2%}",
            )
        self.console.print(table)

    def _write_outputs(self, results: list[ModelBenchmarkResult]) -> Path:
        run_dir = self.config.output_dir / datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        run_dir.mkdir(parents=True, exist_ok=True)
        payload = [result.to_dict() for result in results]
        (run_dir / "scoreboard.json").write_text(json.dumps(payload, indent=2))
        with (run_dir / "scoreboard.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["model", "fit", "llmfit_score", "tps", "ttft", "success_rate", "stability", "context_score", "correctness", "speed_score", "final_score"])
            writer.writeheader()
            for result in results:
                writer.writerow({
                    "model": result.model,
                    "fit": result.fit,
                    "llmfit_score": result.llmfit_score,
                    "tps": result.tps,
                    "ttft": result.ttft,
                    "success_rate": result.success_rate,
                    "stability": result.stability,
                    "context_score": result.context_score,
                    "correctness": result.correctness,
                    "speed_score": result.speed_score,
                    "final_score": result.final_score,
                })
        return run_dir

    @staticmethod
    def _aggregate_invocations(invocations: list[InvocationMetrics]) -> dict[str, float]:
        return {
            "tps": mean(item.tokens_per_second for item in invocations) if invocations else 0.0,
            "ttft": mean(item.ttft_seconds for item in invocations) if invocations else 0.0,
            "latency": mean(item.latency_seconds for item in invocations) if invocations else 0.0,
            "output_tokens": mean(item.output_tokens for item in invocations) if invocations else 0.0,
            "failures": sum(1 for item in invocations if not item.success),
        }

    @staticmethod
    def _task_result_from_dict(payload: dict):
        from benchmark.core.models import TaskResult
        return TaskResult(**payload)

    @staticmethod
    def _metric_list_from_dicts(payload: list[dict]):
        from benchmark.core.models import InvocationMetrics
        return [InvocationMetrics(**item) for item in payload]

    def _latest_run_dir(self) -> Path:
        runs = sorted(path for path in self.config.output_dir.glob("*") if path.is_dir())
        if not runs:
            raise FileNotFoundError("No benchmark runs found.")
        return runs[-1]
