from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Input, Label, Static, TextArea

from core.loop import ExecutionLoop, LoopState
from core.validator import ValidationResult


class TaskApprovalScreen(ModalScreen[list[str] | None]):
    def __init__(self, tasks: list[str]) -> None:
        super().__init__()
        self.tasks = tasks

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Task Approval: edit, remove, or reorder tasks before continuing."),
            TextArea("\n".join(self.tasks), id="task-editor"),
            Horizontal(
                Button("Approve", id="approve", variant="success"),
                Button("Cancel", id="cancel", variant="error"),
            ),
            id="task-approval-dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "approve":
            editor = self.query_one("#task-editor", TextArea)
            tasks = [line.strip() for line in editor.text.splitlines() if line.strip()]
            self.dismiss(tasks)
        else:
            self.dismiss(None)


class PatchReviewScreen(ModalScreen[str]):
    def __init__(self, diff_text: str) -> None:
        super().__init__()
        self.diff_text = diff_text

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Patch Review: accept, reject, or regenerate."),
            TextArea(self.diff_text, read_only=True, id="diff-viewer"),
            Horizontal(
                Button("Accept", id="accept", variant="success"),
                Button("Regenerate", id="regenerate", variant="warning"),
                Button("Reject", id="reject", variant="error"),
            ),
            id="patch-review-dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id or "reject")


class ValidationDecisionScreen(ModalScreen[str]):
    def __init__(self, result: ValidationResult) -> None:
        super().__init__()
        self.result = result

    def compose(self) -> ComposeResult:
        status = "Success" if self.result.success else "Error"
        yield Vertical(
            Label(f"Post-validation Decision ({status})"),
            Static(self.result.output, id="validation-output"),
            Horizontal(
                Button("Continue", id="continue", variant="success"),
                Button("Retry", id="retry", variant="warning"),
                Button("Skip", id="skip"),
                Button("Abort", id="abort", variant="error"),
            ),
            id="validation-dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id or "abort")


class MiniCodexApp(App[None]):
    CSS = """
    Screen { layout: vertical; }
    #main-grid { height: 1fr; }
    #left-col, #right-col { width: 1fr; }
    #request-input, #task-panel, #diff-panel, #logs-panel { height: 1fr; border: round $accent; }
    #status-panel { height: 3; border: round $success; }
    #task-approval-dialog, #patch-review-dialog, #validation-dialog { width: 90%; height: 90%; background: $surface; padding: 1; }
    #diff-viewer, #task-editor { height: 1fr; }
    #validation-output { height: 5; border: round $warning; }
    """

    BINDINGS = [("ctrl+c", "quit", "Quit")]

    def __init__(self) -> None:
        super().__init__()
        self.loop = ExecutionLoop(workspace=Path.cwd())

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(
            Vertical(
                Input(placeholder="Describe what you want mini-Codex to do", id="request-input"),
                TextArea("", id="task-panel", read_only=True),
                id="left-col",
            ),
            Vertical(
                TextArea("", id="diff-panel", read_only=True),
                TextArea("", id="logs-panel", read_only=True),
                id="right-col",
            ),
            id="main-grid",
        )
        yield Static("Status: Idle", id="status-panel")
        yield Horizontal(
            Button("Plan", id="plan", variant="primary"),
            Button("Start", id="start", variant="success"),
            Button("Quit", id="quit", variant="error"),
        )
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_panels(self.loop.state)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "plan":
            request = self.query_one("#request-input", Input).value
            state = self.loop.plan(request)
            self.refresh_panels(state)
            self.push_screen(TaskApprovalScreen(state.tasks), self.handle_task_approval)
        elif event.button.id == "start":
            state = self.loop.start()
            self.refresh_panels(state)
            self.run_current_task()
        elif event.button.id == "quit":
            self.exit()

    def handle_task_approval(self, tasks: list[str] | None) -> None:
        if tasks is None:
            self.loop.abort()
            self.refresh_panels(self.loop.state)
            return
        self.loop.set_tasks(tasks)
        self.refresh_panels(self.loop.state)

    def run_current_task(self) -> None:
        state, diff = self.loop.build_next_patch()
        self.refresh_panels(state, diff_text=diff)
        if state.status == "Completed":
            return
        self.push_screen(PatchReviewScreen(diff), self.handle_patch_review)

    def handle_patch_review(self, decision: str) -> None:
        if decision == "accept":
            state = self.loop.apply_patch()
            self.refresh_panels(state)
            state, result = self.loop.validate()
            self.refresh_panels(state)
            self.push_screen(ValidationDecisionScreen(result), self.handle_validation_decision)
        elif decision == "regenerate":
            self.loop.log("User requested patch regeneration.")
            self.loop.retry()
            self.refresh_panels(self.loop.state)
            self.run_current_task()
        else:
            self.loop.abort()
            self.refresh_panels(self.loop.state)

    def handle_validation_decision(self, decision: str) -> None:
        if decision == "continue":
            state = self.loop.continue_after_validation()
            self.refresh_panels(state)
            if state.status != "Completed":
                self.run_current_task()
        elif decision == "retry":
            state = self.loop.retry()
            self.refresh_panels(state)
            self.run_current_task()
        elif decision == "skip":
            state = self.loop.skip_task()
            self.refresh_panels(state)
            if state.status != "Completed":
                self.run_current_task()
        else:
            state = self.loop.abort()
            self.refresh_panels(state)

    def refresh_panels(self, state: LoopState, diff_text: str | None = None) -> None:
        self.query_one("#task-panel", TextArea).text = "\n".join(state.tasks)
        if diff_text is not None:
            self.query_one("#diff-panel", TextArea).text = diff_text
        self.query_one("#logs-panel", TextArea).text = "\n".join(state.logs[-50:])
        self.query_one("#status-panel", Static).update(
            f"Status: {state.status} | Current task: {state.current_task or '-'} | Attempt: {state.attempt_count}"
        )


def main() -> None:
    MiniCodexApp().run()


if __name__ == "__main__":
    main()
