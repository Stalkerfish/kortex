from __future__ import annotations

from pathlib import Path
import json
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - optional until YAML config is used
    yaml = None

from benchmark.core.models import BenchmarkConfig


DEFAULT_CONFIG = {
    "use_cases": ["coding"],
    "output_dir": "./benchmark_runs",
    "cache_dir": "./.benchmark_cache",
    "max_models": 5,
    "parallelism": 1,
    "iterations": 1,
    "ollama_binary": "ollama",
    "llmfit_binary": "llmfit",
    "weights": {
        "correctness": 0.4,
        "speed": 0.2,
        "context_performance": 0.2,
        "stability": 0.2,
    },
    "task_settings": {
        "code_edit": {"enabled": True},
        "reasoning": {"enabled": True},
        "long_context": {"enabled": True, "repeat_factor": 180},
        "iterative_loop": {"enabled": True, "turns": 4},
    },
    "runner": {
        "timeout_seconds": 180,
        "env": {},
        "api_url": None,
    },
}


def load_config(path: str | Path | None) -> BenchmarkConfig:
    if path is None:
        payload = DEFAULT_CONFIG
    else:
        cfg_path = Path(path)
        text = cfg_path.read_text()
        if cfg_path.suffix.lower() == ".json":
            payload = json.loads(text)
        else:
            if yaml is None:
                raise ModuleNotFoundError("PyYAML is required to load YAML config files.")
            payload = yaml.safe_load(text)

    merged = DEFAULT_CONFIG | payload
    merged["weights"] = DEFAULT_CONFIG["weights"] | merged.get("weights", {})
    merged["task_settings"] = DEFAULT_CONFIG["task_settings"] | merged.get("task_settings", {})
    merged["runner"] = DEFAULT_CONFIG["runner"] | merged.get("runner", {})

    return BenchmarkConfig(
        use_cases=list(merged["use_cases"]),
        output_dir=Path(merged["output_dir"]),
        cache_dir=Path(merged["cache_dir"]),
        max_models=int(merged["max_models"]),
        parallelism=int(merged["parallelism"]),
        iterations=int(merged["iterations"]),
        ollama_binary=str(merged["ollama_binary"]),
        llmfit_binary=str(merged["llmfit_binary"]),
        weights=dict(merged["weights"]),
        task_settings=dict(merged["task_settings"]),
        runner=dict(merged["runner"]),
    )


def dump_default_config(path: str | Path) -> None:
    target = Path(path)
    if yaml is None:
        raise ModuleNotFoundError("PyYAML is required to write YAML config files.")
    target.write_text(yaml.safe_dump(DEFAULT_CONFIG, sort_keys=False))
