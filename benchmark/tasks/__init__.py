from benchmark.tasks.code_edit import CodeEditTask
from benchmark.tasks.iterative_loop import IterativeLoopTask
from benchmark.tasks.long_context import LongContextTask
from benchmark.tasks.reasoning import ReasoningTask


def build_tasks(task_settings: dict) -> list:
    tasks = []
    if task_settings.get("code_edit", {}).get("enabled", True):
        tasks.append(CodeEditTask())
    if task_settings.get("reasoning", {}).get("enabled", True):
        tasks.append(ReasoningTask())
    if task_settings.get("long_context", {}).get("enabled", True):
        tasks.append(LongContextTask(repeat_factor=int(task_settings.get("long_context", {}).get("repeat_factor", 180))))
    if task_settings.get("iterative_loop", {}).get("enabled", True):
        tasks.append(IterativeLoopTask(turns=int(task_settings.get("iterative_loop", {}).get("turns", 4))))
    return tasks
