from benchmark.core.config import load_config


def test_load_default_config():
    cfg = load_config(None)
    assert cfg.use_cases == ["coding"]
    assert cfg.weights["correctness"] == 0.4
