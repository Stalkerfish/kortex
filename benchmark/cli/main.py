from __future__ import annotations

import argparse
import json
from benchmark.core.ui import Console

from benchmark.core.benchmark import BenchmarkOrchestrator
from benchmark.core.config import dump_default_config, load_config
from benchmark.core.logging import configure_logging

console = Console()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="benchmark", description="Local LLM benchmarking for Ollama + aider workflows")
    parser.add_argument("--config", help="Path to YAML/JSON config file", default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List llmfit-recommended candidate models")
    sub.add_parser("run", help="Run the full benchmark suite")

    compare = sub.add_parser("compare", help="Compare models from the latest scoreboard")
    compare.add_argument("models", nargs="+", help="Model names to compare")

    top = sub.add_parser("top", help="Show top models from the latest scoreboard")
    top.add_argument("--category", default=None)
    top.add_argument("--limit", type=int, default=5)

    init_cfg = sub.add_parser("init-config", help="Write an example benchmark config")
    init_cfg.add_argument("path", help="Output config path")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "init-config":
        dump_default_config(args.path)
        console.print(f"Wrote example config to {args.path}")
        return

    config = load_config(args.config)
    configure_logging(config.output_dir)
    orchestrator = BenchmarkOrchestrator(config)

    if args.command == "list":
        console.print_json(json.dumps(orchestrator.list_candidates()))
    elif args.command == "run":
        _, run_dir = orchestrator.run()
        console.print(f"Results written to {run_dir}")
    elif args.command == "compare":
        console.print_json(json.dumps(orchestrator.compare(args.models)))
    elif args.command == "top":
        console.print_json(json.dumps(orchestrator.top(args.category, args.limit)))


if __name__ == "__main__":
    main()
