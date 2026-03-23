from benchmark.core.models import ModelCandidate, TaskResult
from benchmark.scoring.engine import ScoreEngine


def test_score_engine_combines_metrics():
    engine = ScoreEngine({
        "correctness": 0.4,
        "speed": 0.2,
        "context_performance": 0.2,
        "stability": 0.2,
    })
    candidate = ModelCandidate(name="demo", fit="good", llmfit_score=0.8, source_use_cases=["coding"])
    tasks = [
        TaskResult("a", "coding", 1.0, 0.8, 0.7, 0.9, 40.0),
        TaskResult("b", "reasoning", 0.5, 0.6, 0.5, 0.7, 30.0),
    ]
    result = engine.score(candidate, tasks, {"tps": 35.0, "ttft": 2.0})
    assert 0.0 < result.final_score <= 1.0
    assert result.model == "demo"
