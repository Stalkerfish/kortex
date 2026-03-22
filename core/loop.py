from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from core.applier import Applier
from core.builder import Builder
from core.planner import Planner
from core.validator import Validator


@dataclass
class LoopState:
    request: str = ""
    tasks: list[str] = field(default_factory=list)
    current_task_index: int = -1
    attempt_count: int = 0
    last_patch: dict | None = None
    last_error: str | None = None
    status: str = "Idle"
    logs: list[str] = field(default_factory=list)

    @property
    def current_task(self) -> str | None:
        if 0 <= self.current_task_index < len(self.tasks):
            return self.tasks[self.current_task_index]
        return None


class ExecutionLoop:
    def __init__(self, workspace: Path, max_retries: int = 2) -> None:
        self.workspace = workspace
        self.max_retries = max_retries
        self.state = LoopState()
        self.planner = Planner()
        self.builder = Builder(workspace=workspace)
        self.applier = Applier(workspace=workspace)
        self.validator = Validator(workspace=workspace)

    def plan(self, request: str) -> LoopState:
        self.state = LoopState(request=request, status="Planning")
        self.state.tasks = self.planner.create_tasks(request)
        self.log(f"Planned {len(self.state.tasks)} task(s).")
        self.state.status = "Waiting for task approval"
        return self.state

    def set_tasks(self, tasks: list[str]) -> LoopState:
        self.state.tasks = tasks
        self.log("Task list updated by user.")
        return self.state

    def start(self) -> LoopState:
        self.state.current_task_index = 0
        self.state.attempt_count = 0
        self.state.last_error = None
        self.state.status = "Generating patch"
        self.log("Execution started.")
        return self.state

    def build_next_patch(self) -> tuple[LoopState, str]:
        task = self.state.current_task
        if task is None:
            self.state.status = "Completed"
            self.log("No remaining tasks.")
            return self.state, ""
        self.state.attempt_count += 1
        self.state.status = f"Generating patch for task {self.state.current_task_index + 1}"
        self.log(f"Building patch for task: {task}")
        self.state.last_patch = self.builder.generate_patch(self.state.request, task, self.state.last_error)
        diff = self.applier.diff_from_patch(self.state.last_patch)
        self.state.status = "Waiting for patch review"
        return self.state, diff

    def apply_patch(self) -> LoopState:
        if not self.state.last_patch:
            raise RuntimeError("No patch to apply.")
        self.applier.apply(self.state.last_patch)
        self.state.status = "Validating"
        self.log("Patch applied.")
        return self.state

    def validate(self) -> tuple[LoopState, ValidationResult]:
        result = self.validator.validate()
        self.state.last_error = None if result.success else result.output
        self.state.status = "Waiting for validation decision"
        self.log(result.output)
        return self.state, result

    def continue_after_validation(self) -> LoopState:
        self.state.current_task_index += 1
        self.state.attempt_count = 0
        self.state.last_patch = None
        self.state.last_error = None
        if self.state.current_task_index >= len(self.state.tasks):
            self.state.status = "Completed"
            self.log("All tasks completed.")
        else:
            self.state.status = "Generating patch"
            self.log("Advancing to next task.")
        return self.state

    def retry(self) -> LoopState:
        if self.state.attempt_count > self.max_retries:
            self.state.status = "Retry limit reached"
            self.log("Retry limit reached. Awaiting user decision.")
        else:
            self.state.status = "Generating patch"
            self.log("Retrying current task.")
        return self.state

    def skip_task(self) -> LoopState:
        self.log(f"Skipping task: {self.state.current_task}")
        return self.continue_after_validation()

    def abort(self) -> LoopState:
        self.state.status = "Aborted"
        self.log("Execution aborted by user.")
        return self.state

    def log(self, message: str) -> None:
        self.state.logs.append(message)
