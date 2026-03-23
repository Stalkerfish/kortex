from __future__ import annotations

import logging
import subprocess
import time
from typing import Iterable

from benchmark.core.models import InvocationMetrics, PromptTurn

LOGGER = logging.getLogger(__name__)


class OllamaRunner:
    def __init__(self, binary: str = "ollama", timeout_seconds: int = 180, env: dict[str, str] | None = None) -> None:
        self.binary = binary
        self.timeout_seconds = timeout_seconds
        self.env = env

    def invoke(self, model: str, prompt: str, context_turns: Iterable[PromptTurn] | None = None) -> InvocationMetrics:
        effective_prompt = self._compose_prompt(prompt, context_turns or [])
        cmd = [self.binary, "run", model]
        start = time.perf_counter()
        try:
            proc = subprocess.run(
                cmd,
                input=effective_prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                env=self.env,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            latency = time.perf_counter() - start
            return InvocationMetrics(latency, latency, 0.0, 0, "", False, error=f"timeout: {exc}")

        latency = time.perf_counter() - start
        if proc.returncode != 0:
            return InvocationMetrics(latency, latency, 0.0, 0, proc.stdout, False, error=proc.stderr.strip())

        output_text = proc.stdout.strip()
        output_tokens = max(1, len(output_text.split())) if output_text else 0
        ttft = self._infer_ttft(proc.stderr, latency)
        tps = output_tokens / max(latency - min(ttft, latency * 0.8), 1e-6) if output_tokens else 0.0
        return InvocationMetrics(latency, ttft, tps, output_tokens, output_text, True, error=None)

    @staticmethod
    def _compose_prompt(prompt: str, context_turns: Iterable[PromptTurn]) -> str:
        turns = []
        for turn in context_turns:
            turns.append(f"[{turn.role.upper()}]\n{turn.content}")
        turns.append(f"[USER]\n{prompt}")
        return "\n\n".join(turns)

    @staticmethod
    def _infer_ttft(stderr: str, latency: float) -> float:
        for line in stderr.splitlines():
            if "load" in line.lower() and any(ch.isdigit() for ch in line):
                digits = "".join(ch if ch.isdigit() or ch == "." else " " for ch in line).split()
                if digits:
                    try:
                        value = float(digits[0])
                        return min(value, latency)
                    except ValueError:
                        continue
        return min(latency * 0.35, latency)
