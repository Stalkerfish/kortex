# kortex benchmark

A modular local LLM benchmarking and model selection framework designed for **Ollama + aider workflows**. It combines **`llmfit` recommendations as a prior** with **real local measurements** from Ollama to rank models across coding-relevant dimensions.

## Architecture

The system is split into small, replaceable modules:

- `benchmark/core`: config loading, orchestration, caching, logging, shared dataclasses.
- `benchmark/runners`: integrations for `llmfit` candidate discovery and `ollama run` execution.
- `benchmark/tasks`: pluggable benchmark suites for code editing, reasoning, long-context stress, and iterative aider-style loops.
- `benchmark/scoring`: weighted normalization and final ranking logic.
- `benchmark/cli`: commands for listing candidates, running benchmarks, comparing models, and showing top performers.
- `benchmark/examples`: example config to tune weights and task settings.

### Design choices

- **`llmfit` as prior, not truth**: recommendations seed the candidate pool, but local scores are based on real execution.
- **Task modularity**: every task implements a small `BenchmarkTask` interface, so new suites can be added without touching the orchestration flow.
- **Graceful failure handling**: timeouts, crashes, and non-zero exits are converted into structured metrics instead of stopping the whole run.
- **Cache-first reruns**: per-model, per-task cache entries avoid re-running expensive prompts when task settings have not changed.
- **Future routing support**: the resulting JSON scoreboard is designed to feed later routing or live evaluation systems.

## Features

- Candidate generation from `llmfit recommend --json --use-case <category>`.
- Deduplication across use cases such as `coding`, `reasoning`, `general`, and `chat`.
- Ollama benchmark runner capturing latency, inferred TTFT, throughput, output length, and failures.
- Four benchmark suites:
  - Code edit / refactor task.
  - Multi-step reasoning and systems design task.
  - Long-context stress prompt.
  - Iterative multi-turn aider simulation.
- Weighted scoring for correctness, speed, context performance, and stability.
- Output formats:
  - JSON scoreboard.
  - CSV export.
  - Rich terminal table.
- CLI commands:
  - `benchmark init-config`
  - `benchmark list`
  - `benchmark run`
  - `benchmark compare`
  - `benchmark top`

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Dependencies:

- Python 3.10+
- `ollama` available on `PATH`
- `llmfit` available on `PATH`

## Quick start

1. Generate an editable config:

   ```bash
   benchmark init-config benchmark.yaml
   ```

2. Review the example config in `benchmark/examples/config.yaml` or edit your own.

3. Inspect candidates from llmfit:

   ```bash
   benchmark --config benchmark.yaml list
   ```

4. Run the benchmark suite:

   ```bash
   benchmark --config benchmark.yaml run
   ```

5. Inspect winners:

   ```bash
   benchmark --config benchmark.yaml top --category coding --limit 3
   benchmark --config benchmark.yaml compare codellama:13b qwen2.5-coder:7b
   ```

## Scoring

Final score uses configurable weights:

```text
score =
  w_correctness * correctness +
  w_speed * normalized_speed +
  w_context * context_performance +
  w_stability * stability
```

The weighted empirical score is then blended with the `llmfit` prior to avoid throwing away theory-driven recommendations while still favoring observed local performance.

## Example output schema

```json
{
  "model": "qwen2.5-coder:7b",
  "fit": "perfect",
  "llmfit_score": 0.92,
  "tps": 33.4,
  "ttft": 1.8,
  "success_rate": 0.87,
  "stability": 0.82,
  "context_score": 0.78,
  "final_score": 0.81
}
```

## Extending the framework

- Add a new task by implementing `BenchmarkTask` and registering it in `benchmark/tasks/__init__.py`.
- Replace the Ollama runner with the HTTP API or streaming implementation if you want accurate TTFT/token timing.
- Feed `scoreboard.json` into future routing logic, live evaluation loops, or tighter aider automation.

## Notes on metrics

- `ttft` is inferred from `ollama run` behavior because the CLI does not expose streaming token timestamps directly.
- For more precise token telemetry, you can swap the runner to use the Ollama HTTP API with streamed chunk timing.
- Heuristic correctness checks are intentionally lightweight so the framework works offline on a single machine.
