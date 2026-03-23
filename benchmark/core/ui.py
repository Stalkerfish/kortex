from __future__ import annotations

try:
    from rich.console import Console
    from rich.table import Table
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal environments
    class Console:  # type: ignore[override]
        def print(self, obj):
            print(obj)

        def print_json(self, text: str):
            print(text)

    class Table:  # type: ignore[override]
        def __init__(self, title: str | None = None):
            self.title = title
            self.columns: list[str] = []
            self.rows: list[list[str]] = []

        def add_column(self, name: str):
            self.columns.append(name)

        def add_row(self, *values: str):
            self.rows.append(list(values))

        def __str__(self) -> str:
            lines = [self.title] if self.title else []
            if self.columns:
                lines.append(" | ".join(self.columns))
                lines.append("-" * max(3, len(lines[-1])))
            for row in self.rows:
                lines.append(" | ".join(row))
            return "\n".join(lines)
