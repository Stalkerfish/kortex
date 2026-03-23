from __future__ import annotations

from pathlib import Path
import hashlib
import json
from typing import Any


class ResultCache:
    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key_path(self, payload: dict[str, Any]) -> Path:
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        return self.cache_dir / f"{digest}.json"

    def load(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        path = self._key_path(payload)
        if path.exists():
            return json.loads(path.read_text())
        return None

    def save(self, payload: dict[str, Any], value: dict[str, Any]) -> None:
        self._key_path(payload).write_text(json.dumps(value, indent=2))
