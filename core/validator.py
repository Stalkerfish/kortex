from __future__ import annotations

import compileall
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ValidationResult:
    success: bool
    output: str


@dataclass
class Validator:
    workspace: Path

    def validate(self) -> ValidationResult:
        ok = compileall.compile_dir(str(self.workspace), quiet=1)
        message = "Validation passed: Python sources compiled successfully." if ok else "Validation failed: compileall reported errors."
        return ValidationResult(success=ok, output=message)
