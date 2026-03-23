from __future__ import annotations

import json
import logging
import subprocess

from benchmark.core.models import ModelCandidate

LOGGER = logging.getLogger(__name__)
FIT_SCORES = {"perfect": 1.0, "good": 0.8, "marginal": 0.5, "unknown": 0.3}


class LLMFitRunner:
    def __init__(self, binary: str = "llmfit") -> None:
        self.binary = binary

    def recommend(self, use_case: str) -> list[ModelCandidate]:
        cmd = [self.binary, "recommend", "--json", "--use-case", use_case]
        LOGGER.info("Running llmfit recommendation for %s", use_case)
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"llmfit failed for {use_case}: {proc.stderr.strip()}")

        payload = json.loads(proc.stdout)
        models = []
        for item in payload.get("recommendations", payload if isinstance(payload, list) else []):
            fit = str(item.get("fit", "unknown")).lower()
            score = item.get("score", item.get("estimated_score", FIT_SCORES.get(fit, 0.3)))
            models.append(
                ModelCandidate(
                    name=item.get("model") or item.get("name"),
                    fit=fit,
                    llmfit_score=float(score),
                    source_use_cases=[use_case],
                    metadata={
                        "estimated_speed": item.get("estimated_speed"),
                        "raw": item,
                    },
                )
            )
        return models


def merge_candidates(candidates: list[ModelCandidate], max_models: int | None = None) -> list[ModelCandidate]:
    merged: dict[str, ModelCandidate] = {}
    for candidate in candidates:
        if candidate.name in merged:
            existing = merged[candidate.name]
            existing.llmfit_score = max(existing.llmfit_score, candidate.llmfit_score)
            existing.source_use_cases = sorted(set(existing.source_use_cases + candidate.source_use_cases))
            if FIT_SCORES.get(candidate.fit, 0) > FIT_SCORES.get(existing.fit, 0):
                existing.fit = candidate.fit
        else:
            merged[candidate.name] = candidate

    ordered = sorted(merged.values(), key=lambda item: item.llmfit_score, reverse=True)
    return ordered[:max_models] if max_models else ordered
